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
        # Clean and normalize text
        text = TranscriptParser._clean_text(text)
        
        return {
            "format": "plain_text",
            "text": text,
            "speakers": [],
            "segments": [{"speaker": "Unknown", "text": text}]
        }
    
    @staticmethod
    def _parse_dict(data: Dict) -> Dict:
        """Parse dictionary/JSON transcript."""
        # Check for common JSON transcript formats
        if "speakers" in data or "segments" in data or "transcript" in data:
            return TranscriptParser._parse_speaker_tagged(data)
        else:
            # Treat as plain text stored in dict
            text = str(data.get("text", data.get("content", "")))
            text = TranscriptParser._clean_text(text)
            return {
                "format": "json",
                "text": text,
                "speakers": [],
                "segments": [{"speaker": "Unknown", "text": text}]
            }
    
    @staticmethod
    def _parse_speaker_tagged(data: Dict) -> Dict:
        """Parse speaker-tagged transcript."""
        segments = []
        speakers = set()
        full_text_parts = []
        
        # Handle different JSON formats
        if "segments" in data:
            segments_data = data["segments"]
        elif "transcript" in data:
            segments_data = data["transcript"]
        else:
            # Try to infer structure
            segments_data = data
        
        if isinstance(segments_data, list):
            for segment in segments_data:
                if isinstance(segment, dict):
                    speaker = segment.get("speaker", segment.get("name", "Unknown"))
                    text = segment.get("text", segment.get("content", ""))
                    timestamp = segment.get("timestamp", segment.get("time", None))
                else:
                    speaker = "Unknown"
                    text = str(segment)
                    timestamp = None
                
                text = TranscriptParser._clean_text(text)
                if text:
                    segments.append({
                        "speaker": speaker,
                        "text": text,
                        "timestamp": timestamp
                    })
                    speakers.add(speaker)
                    full_text_parts.append(f"{speaker}: {text}")
        else:
            # Single text block
            text = TranscriptParser._clean_text(str(segments_data))
            segments.append({"speaker": "Unknown", "text": text})
            full_text_parts.append(text)
        
        return {
            "format": "speaker_tagged",
            "text": "\n".join(full_text_parts),
            "speakers": list(speakers),
            "segments": segments
        }
    
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


