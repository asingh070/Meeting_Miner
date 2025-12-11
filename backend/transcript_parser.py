"""Transcript parser for plain text and JSON formats."""
import json
import re
from typing import Dict, List, Optional, Union
from backend.logger import logger


class TranscriptParser:
    """Parse and normalize meeting transcripts."""
    
    @staticmethod
    def parse(transcript: Union[str, Dict]) -> Dict:
        """
        Parse transcript from various formats.
        
        Args:
            transcript: Can be:
                - Plain text string
                - JSON string
                - Dictionary with speaker-tagged format
        
        Returns:
            Dictionary with normalized transcript data
        """
        if isinstance(transcript, dict):
            return TranscriptParser._parse_dict(transcript)
        elif isinstance(transcript, str):
            # Try to parse as JSON first
            try:
                data = json.loads(transcript)
                return TranscriptParser._parse_dict(data)
            except json.JSONDecodeError:
                # Treat as plain text
                return TranscriptParser._parse_plain_text(transcript)
        else:
            error_msg = f"Unsupported transcript type: {type(transcript)}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)
    
    @staticmethod
    def _parse_plain_text(text: str) -> Dict:
        """Parse plain text transcript."""
        # Check if text contains speaker-tagged format (e.g., "Speaker: text")
        lines = text.split('\n')
        segments = []
        speakers = set()
        full_text_parts = []
        extracted_title = None
        
        # Pattern to match "Speaker: text" format
        speaker_pattern = re.compile(r'^([A-Za-z][A-Za-z\s]+?):\s*(.+)$')
        # Pattern to match "Meeting ID:" or title lines
        title_pattern = re.compile(r'^(Meeting ID|Title):\s*(.+)$', re.IGNORECASE)
        
        has_speaker_tags = False
        skip_next_empty = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                if skip_next_empty:
                    skip_next_empty = False
                continue
            
            # Check for title/metadata lines (usually at the start)
            if i < 3:  # Check first few lines for title/metadata
                title_match = title_pattern.match(line)
                if title_match:
                    if "meeting id" in line.lower():
                        # Skip meeting ID line
                        skip_next_empty = True
                        continue
                    elif "title" in line.lower():
                        extracted_title = title_match.group(2).strip()
                        skip_next_empty = True
                        continue
                # If first line doesn't match speaker pattern and looks like a title
                elif i == 0 and not speaker_pattern.match(line) and len(line) < 100:
                    extracted_title = line
                    skip_next_empty = True
                    continue
            
            # Try to match speaker pattern
            match = speaker_pattern.match(line)
            if match:
                has_speaker_tags = True
                speaker = match.group(1).strip()
                text_content = match.group(2).strip()
                
                if text_content:
                    text_content = TranscriptParser._clean_text(text_content)
                    if text_content:
                        segments.append({
                            "speaker": speaker,
                            "text": text_content
                        })
                        speakers.add(speaker)
                        full_text_parts.append(f"{speaker}: {text_content}")
            else:
                # If we've seen speaker tags before, this might be continuation
                if has_speaker_tags and segments:
                    # Append to last segment
                    if segments:
                        cleaned_line = TranscriptParser._clean_text(line)
                        if cleaned_line:
                            segments[-1]["text"] += " " + cleaned_line
                            full_text_parts[-1] = f"{segments[-1]['speaker']}: {segments[-1]['text']}"
                else:
                    # No speaker tags, treat as plain text
                    full_text_parts.append(line)
        
        if has_speaker_tags and segments:
            # Speaker-tagged format detected
            result = {
                "format": "speaker_tagged",
                "text": "\n".join(full_text_parts),
                "speakers": list(speakers),
                "segments": segments
            }
            if extracted_title:
                result["title"] = extracted_title
            return result
        else:
            # Plain text format
            cleaned_text = TranscriptParser._clean_text(text)
            result = {
                "format": "plain_text",
                "text": cleaned_text,
                "speakers": [],
                "segments": [{"speaker": "Unknown", "text": cleaned_text}]
            }
            if extracted_title:
                result["title"] = extracted_title
            return result
    
    @staticmethod
    def _parse_dict(data: Dict) -> Dict:
        """Parse dictionary/JSON transcript."""
        # Check for new format with meeting_id, title, and segments
        if "segments" in data and isinstance(data.get("segments"), list):
            return TranscriptParser._parse_speaker_tagged(data)
        # Check for common JSON transcript formats
        elif "speakers" in data or "transcript" in data:
            return TranscriptParser._parse_speaker_tagged(data)
        else:
            # Treat as plain text stored in dict
            text = str(data.get("text", data.get("content", "")))
            text = TranscriptParser._clean_text(text)
            return {
                "format": "json",
                "text": text,
                "speakers": [],
                "segments": [{"speaker": "Unknown", "text": text}],
                "meeting_id": None,
                "title": None
            }
    
    @staticmethod
    def _parse_speaker_tagged(data: Dict) -> Dict:
        """Parse speaker-tagged transcript."""
        segments = []
        speakers = set()
        full_text_parts = []
        
        # Extract meeting_id and title if present (new format)
        meeting_id = data.get("meeting_id")
        title = data.get("title")
        language_hint = data.get("language_hint", "auto")
        
        # Handle different JSON formats
        if "segments" in data:
            segments_data = data["segments"]
        elif "transcript" in data:
            segments_data = data["transcript"]
        else:
            # Try to infer structure
            segments_data = data
        
        if isinstance(segments_data, list):
            if len(segments_data) == 0:
                # Empty segments array - return empty result
                logger.warning("Empty segments array in transcript JSON")
                return {
                    "format": "speaker_tagged",
                    "text": "",
                    "speakers": [],
                    "segments": [],
                    "meeting_id": meeting_id,
                    "title": title,
                    "language_hint": language_hint
                }
            
            for segment in segments_data:
                if isinstance(segment, dict):
                    speaker = segment.get("speaker", segment.get("name", "Unknown"))
                    text = segment.get("text", segment.get("content", ""))
                    # Handle timestamp formats: timestamp, time, start/end
                    timestamp = segment.get("timestamp") or segment.get("time")
                    start_time = segment.get("start")
                    end_time = segment.get("end")
                else:
                    speaker = "Unknown"
                    text = str(segment)
                    timestamp = None
                    start_time = None
                    end_time = None
                
                text = TranscriptParser._clean_text(text)
                if text:
                    segment_dict = {
                        "speaker": speaker,
                        "text": text
                    }
                    # Add timestamp information if available
                    if timestamp:
                        segment_dict["timestamp"] = timestamp
                    if start_time:
                        segment_dict["start"] = start_time
                    if end_time:
                        segment_dict["end"] = end_time
                    
                    segments.append(segment_dict)
                    speakers.add(speaker)
                    full_text_parts.append(f"{speaker}: {text}")
        else:
            # Single text block
            text = TranscriptParser._clean_text(str(segments_data))
            segments.append({"speaker": "Unknown", "text": text})
            full_text_parts.append(text)
        
        result = {
            "format": "speaker_tagged",
            "text": "\n".join(full_text_parts),
            "speakers": list(speakers),
            "segments": segments
        }
        
        # Add meeting metadata if present
        if meeting_id:
            result["meeting_id"] = meeting_id
        if title:
            result["title"] = title
        if language_hint:
            result["language_hint"] = language_hint
        
        return result
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere (but keep punctuation)
        text = text.strip()
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text
    
    @staticmethod
    def get_full_text(parsed: Dict) -> str:
        """Extract full text from parsed transcript."""
        return parsed.get("text", "")
    
    @staticmethod
    def get_speakers(parsed: Dict) -> List[str]:
        """Extract list of speakers from parsed transcript."""
        return parsed.get("speakers", [])
    
    @staticmethod
    def get_segments(parsed: Dict) -> List[Dict]:
        """Extract segments from parsed transcript."""
        return parsed.get("segments", [])
    
    @staticmethod
    def get_meeting_id(parsed: Dict) -> Optional[str]:
        """Extract meeting_id from parsed transcript if present."""
        return parsed.get("meeting_id")
    
    @staticmethod
    def get_title(parsed: Dict) -> Optional[str]:
        """Extract title from parsed transcript if present."""
        return parsed.get("title")
    
    @staticmethod
    def get_language_hint(parsed: Dict) -> str:
        """Extract language_hint from parsed transcript, defaults to 'auto'."""
        return parsed.get("language_hint", "auto")


