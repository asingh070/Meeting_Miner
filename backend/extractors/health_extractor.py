"""Project health signals extractor."""
from typing import Dict, List, Optional
from backend.llm import get_llm_client
from backend.logger import logger


class HealthExtractor:
    """Extract project health signals (owners, blockers, risks) for the MAIN project."""
    
    SYSTEM_PROMPT = """You are an expert at identifying project health signals from meeting conversations.

Your task is to identify:
1. Project owners and assignees
2. Blockers and impediments
3. Risks and concerns
4. Commitment signals (including non-committal responses like "haan yaar, dekh lenge" which might indicate potential blockers)

The transcript may contain Hinglish (Hindi-English mix) or other multilingual content. Pay special attention to:
- Non-committal responses ("we'll see", "dekhenge", "maybe")
- Hesitation or uncertainty
- Explicit blockers mentioned
- Risk indicators

Return a JSON object with the following structure:
{
  "owners": ["Person 1", "Person 2"],
  "blockers": [
    {
      "description": "Blocker description",
      "project": "Project name (if applicable)",
      "severity": "high|medium|low"
    }
  ],
  "risks": [
    {
      "description": "Risk description",
      "project": "Project name (if applicable)",
      "severity": "high|medium|low"
    }
  ],
  "commitment_signals": [
    {
      "text": "The actual phrase or statement",
      "interpretation": "What it likely means",
      "project": "Project name (if applicable)"
    }
  ]
}"""

    def __init__(self):
        """Initialize extractor."""
        self.llm = get_llm_client()
    
    def extract(self, transcript_text: str, main_project_name: Optional[str] = None) -> Dict:
        """
        Extract health signals from transcript.
        
        Args:
            transcript_text: Full meeting transcript text
            main_project_name: Optional main project name (for reference, but extract all health signals)
        
        Returns:
            Dictionary with owners, blockers, risks, and commitment signals
        """
        prompt = f"""Analyze the following meeting transcript and extract project health signals.

Look for:
- People assigned to projects or tasks (owners)
- Blockers and impediments mentioned
- Risks and concerns raised
- Non-committal or hesitant responses (like "haan yaar, dekh lenge", "we'll see", "maybe")

Pay special attention to phrases that might indicate lack of commitment or potential blockers disguised as optimism.

Transcript:
{transcript_text}

Return a JSON object with health signals."""

        try:
            result = self.llm.generate_json(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.3
            )
            
            # Normalize structure
            normalized = {
                "owners": result.get("owners", []),
                "blockers": result.get("blockers", []),
                "risks": result.get("risks", []),
                "commitment_signals": result.get("commitment_signals", [])
            }
            
            return normalized
        except Exception as e:
            # Fallback to empty structure on error
            error_msg = f"Error extracting health signals: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            return {
                "owners": [],
                "blockers": [],
                "risks": [],
                "commitment_signals": []
            }


