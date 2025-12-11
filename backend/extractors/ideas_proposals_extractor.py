"""Ideas and proposals extractor (optional - only when ideas/proposals can be built)."""
from typing import Dict, List, Optional
from backend.llm import get_llm_client
from backend.logger import logger


class IdeasProposalsExtractor:
    """Extract ideas and proposals that can be built from meeting conversations."""
    
    SYSTEM_PROMPT = """You are an expert at identifying actionable ideas, proposals, and opportunities from meeting conversations.

Your task is to identify:
1. Ideas or proposals mentioned that could be developed into projects or initiatives
2. Opportunities discussed that could be pursued
3. Suggestions or recommendations that could be actionable
4. Innovation opportunities or improvements suggested

IMPORTANT: Only extract ideas/proposals if they are:
- Explicitly mentioned or discussed
- Have enough detail to be actionable
- Could realistically be built or implemented

If no clear ideas or proposals are present, return an empty array.

The transcript may contain Hinglish (Hindi-English mix) or other multilingual content. Understand and process it correctly.

Return a JSON object with an "ideas" key containing an array with the following structure:
{
  "ideas": [
    {
      "idea": "Description of the idea or proposal",
      "description": "Detailed description of what could be built",
      "potential_value": "Why this idea is valuable or what problem it solves",
      "feasibility": "high|medium|low",
      "suggested_by": "Person who suggested it (if mentioned)",
      "related_project": "Related project name (if applicable)"
    }
  ]
}

If no ideas or proposals can be identified, return {"ideas": []}."""

    def __init__(self):
        """Initialize extractor."""
        self.llm = get_llm_client()
    
    def extract(self, transcript_text: str) -> List[Dict]:
        """
        Extract ideas and proposals from transcript.
        
        Args:
            transcript_text: Full meeting transcript text
        
        Returns:
            List of idea/proposal dictionaries (empty if none found)
        """
        prompt = f"""Analyze the following meeting transcript and identify any ideas, proposals, or opportunities that could be built or implemented.

Look for:
- Ideas or suggestions mentioned
- Proposals for new initiatives or improvements
- Opportunities discussed
- Innovation opportunities
- Actionable recommendations

IMPORTANT: Only extract ideas/proposals if they are clearly mentioned and have enough detail to be actionable. If no clear ideas or proposals are present, return an empty array.

Transcript:
{transcript_text}

Return a JSON object with an "ideas" key containing an array of ideas/proposals. If none are found, return {{"ideas": []}}."""

        try:
            result = self.llm.generate_json(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.4
            )
            
            # Handle different response formats
            if isinstance(result, dict):
                if "ideas" in result:
                    ideas = result["ideas"]
                elif "proposals" in result:
                    ideas = result["proposals"]
                elif "data" in result:
                    ideas = result["data"]
                else:
                    ideas = []
            elif isinstance(result, list):
                ideas = result
            else:
                ideas = []
            
            # Normalize structure
            normalized_ideas = []
            for idea in ideas:
                if isinstance(idea, dict):
                    normalized_ideas.append({
                        "idea": idea.get("idea", ""),
                        "description": idea.get("description", ""),
                        "potential_value": idea.get("potential_value", ""),
                        "feasibility": idea.get("feasibility", "medium"),
                        "suggested_by": idea.get("suggested_by", ""),
                        "related_project": idea.get("related_project", "")
                    })
            
            return normalized_ideas
        except Exception as e:
            # Fallback to empty list on error
            error_msg = f"Error extracting ideas/proposals: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            return []

