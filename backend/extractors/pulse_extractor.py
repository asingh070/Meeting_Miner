"""Company pulse extractor (sentiment, tone, behavioral cues)."""
from typing import Dict, List
from backend.llm import get_llm_client
from backend.logger import logger


class PulseExtractor:
    """Extract company pulse (sentiment, tone, behavioral cues)."""
    
    SYSTEM_PROMPT = """You are an expert at analyzing meeting dynamics and extracting company pulse indicators.

Your task is to analyze:
1. Overall sentiment (positive, neutral, negative)
2. Tone detection (optimistic, cautious, frustrated, enthusiastic)
3. Behavioral cues (engagement levels, participation patterns)
4. Per-speaker sentiment (if speakers are identified)
5. Team dynamics and collaboration signals

The transcript may contain Hinglish (Hindi-English mix) or other multilingual content. Understand cultural context and communication patterns.

Return a JSON object with the following structure:
{
  "overall_sentiment": "positive|neutral|negative",
  "sentiment_score": 0.0 to 1.0 (0 = very negative, 1 = very positive),
  "tone": ["optimistic", "cautious", "frustrated", etc.],
  "speaker_sentiments": [
    {
      "speaker": "Speaker name",
      "sentiment": "positive|neutral|negative",
      "sentiment_score": 0.0 to 1.0,
      "engagement_level": "high|medium|low"
    }
  ],
  "behavioral_cues": [
    {
      "cue": "Description of behavioral pattern",
      "type": "engagement|collaboration|conflict|alignment"
    }
  ],
  "key_insights": ["Insight 1", "Insight 2"]
}"""

    def __init__(self):
        """Initialize extractor."""
        self.llm = get_llm_client()
    
    def extract(self, transcript_text: str, speakers: List[str] = None) -> Dict:
        """
        Extract company pulse from transcript.
        
        Args:
            transcript_text: Full meeting transcript text
            speakers: Optional list of speaker names
        
        Returns:
            Dictionary with sentiment, tone, and behavioral analysis
        """
        speakers_context = ""
        if speakers:
            speakers_context = f"\n\nSpeakers identified in the meeting: {', '.join(speakers)}"
        
        prompt = f"""Analyze the following meeting transcript and extract company pulse indicators.

Analyze:
- Overall sentiment and tone
- Individual speaker sentiments and engagement (if speakers are identified)
- Behavioral patterns and team dynamics
- Key insights about team morale and collaboration

{speakers_context}

Transcript:
{transcript_text}

Return a JSON object with pulse analysis."""

        try:
            result = self.llm.generate_json(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.4
            )
            
            # Normalize structure
            normalized = {
                "overall_sentiment": result.get("overall_sentiment", "neutral"),
                "sentiment_score": float(result.get("sentiment_score", 0.5)),
                "tone": result.get("tone", []),
                "speaker_sentiments": result.get("speaker_sentiments", []),
                "behavioral_cues": result.get("behavioral_cues", []),
                "key_insights": result.get("key_insights", [])
            }
            
            # Ensure sentiment_score is in valid range
            normalized["sentiment_score"] = max(0.0, min(1.0, normalized["sentiment_score"]))
            
            return normalized
        except Exception as e:
            # Fallback to neutral structure on error
            error_msg = f"Error extracting pulse: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.5,
                "tone": [],
                "speaker_sentiments": [],
                "behavioral_cues": [],
                "key_insights": []
            }


