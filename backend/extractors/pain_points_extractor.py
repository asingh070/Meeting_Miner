"""Project-specific pain points extractor."""
from typing import Dict, List, Optional
from backend.llm import get_llm_client
from backend.logger import logger


class PainPointsExtractor:
    """Extract project-specific pain points from meeting transcript."""
    
    SYSTEM_PROMPT = """You are an expert at identifying pain points, challenges, and problems mentioned in meeting conversations.

Your task is to identify:
1. Project-specific pain points (challenges related to specific projects or initiatives)
2. General pain points (organizational, process, or team-level issues)
3. Pain point details: description, affected project/area, severity, impact

The transcript may contain Hinglish (Hindi-English mix) or other multilingual content. Understand phrases that indicate problems, frustrations, or challenges.

Return a JSON object with the following structure:
{
  "project_specific": [
    {
      "project": "Project name (if mentioned)",
      "pain_point": "Description of the pain point",
      "severity": "high|medium|low",
      "impact": "Description of impact"
    }
  ],
  "general": [
    {
      "pain_point": "Description of the pain point",
      "category": "process|tool|team|resource|other",
      "severity": "high|medium|low",
      "impact": "Description of impact"
    }
  ]
}"""

    def __init__(self):
        """Initialize extractor."""
        self.llm = get_llm_client()
    
    def extract(self, transcript_text: str, main_project_name: Optional[str] = None) -> Dict:
        """
        Extract pain points from transcript.
        
        Args:
            transcript_text: Full meeting transcript text
            main_project_name: Optional main project name (for reference, but extract all pain points)
        
        Returns:
            Dictionary with project-specific and general pain points
        """
        prompt = f"""Analyze the following meeting transcript and identify all pain points, challenges, and problems mentioned.

Look for:
- Project-specific challenges or blockers
- General organizational or process issues
- Frustrations or concerns expressed
- Problems that need to be addressed
- Areas of difficulty or struggle

Be thorough in identifying pain points, even if they're mentioned briefly or indirectly.

Transcript:
{transcript_text}

Return a JSON object with pain points analysis."""

        try:
            result = self.llm.generate_json(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.3
            )
            
            # Normalize structure
            normalized = {
                "project_specific": result.get("project_specific", []),
                "general": result.get("general", [])
            }
            
            return normalized
        except Exception as e:
            # Fallback to empty structure on error
            error_msg = f"Error extracting pain points: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            return {
                "project_specific": [],
                "general": []
            }

