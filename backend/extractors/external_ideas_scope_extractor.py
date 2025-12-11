"""External ideas and scope extractor - identifies additional projects/ideas that can be built."""
from typing import Dict, List
from backend.llm import get_llm_client
from backend.logger import logger


class ExternalIdeasScopeExtractor:
    """Extract external ideas and scope that can be built based on meeting conversations."""
    
    SYSTEM_PROMPT = """You are an expert at identifying external ideas, opportunities, and scope for new projects or initiatives from meeting conversations.

Your task is to identify:
1. External ideas or projects that can be built based on discussions
2. Additional scope or opportunities mentioned that are separate from the main project
3. Ideas for new initiatives, features, or products discussed
4. Opportunities that emerged from side conversations or tangential discussions
5. Potential projects that could be created based on the meeting content

IMPORTANT: Focus on EXTERNAL ideas - things that are ADDITIONAL to the main project being discussed. These should be:
- New initiatives or projects that could be built
- Additional features or products mentioned
- Opportunities for expansion or new work
- Ideas that emerged from discussions but aren't part of the main project

The transcript may contain Hinglish (Hindi-English mix) or other multilingual content. Understand and process it correctly.

Return a JSON object with a "ideas" key containing an array with the following structure:
{
  "ideas": [
    {
      "idea": "Name or title of the idea/project",
      "description": "Detailed description of what could be built",
      "scope": "The scope and potential of this idea",
      "feasibility": "high|medium|low",
      "potential_value": "Why this idea is valuable or what problem it solves",
      "suggested_by": "Person who suggested it (if mentioned)",
      "related_to": "How it relates to the main discussion (if applicable)"
    }
  ]
}

If no external ideas or scope are identified, return {"ideas": []}."""

    def __init__(self):
        """Initialize extractor."""
        self.llm = get_llm_client()
    
    def extract(self, transcript_text: str) -> List[Dict]:
        """
        Extract external ideas and scope from transcript.
        
        Args:
            transcript_text: Full meeting transcript text
        
        Returns:
            List of external idea/scope dictionaries
        """
        prompt = f"""Analyze the following meeting transcript and identify EXTERNAL ideas, opportunities, and scope for new projects or initiatives that can be built.

Focus on:
- Ideas for NEW projects or initiatives (separate from the main project)
- Additional scope or opportunities mentioned
- Features or products that could be created
- Opportunities that emerged from discussions
- Side conversations that suggest new work

IMPORTANT: Only extract EXTERNAL ideas - things that are ADDITIONAL to the main project. These should be opportunities for NEW work, not part of the current project scope.

Look for:
- "We could also build..."
- "What if we created..."
- "Another idea would be..."
- Side discussions about new features or products
- Opportunities for expansion
- Ideas that go beyond the main project scope

Transcript:
{transcript_text}

Return a JSON object with an "ideas" key containing an array of external ideas/scope. If no external ideas are found, return {{"ideas": []}}."""

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
                elif "scope" in result:
                    ideas = result["scope"]
                elif "external_ideas" in result:
                    ideas = result["external_ideas"]
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
                        "scope": idea.get("scope", ""),
                        "feasibility": idea.get("feasibility", "medium"),
                        "potential_value": idea.get("potential_value", ""),
                        "suggested_by": idea.get("suggested_by", ""),
                        "related_to": idea.get("related_to", "")
                    })
            
            return normalized_ideas
        except Exception as e:
            # Fallback to empty list on error
            error_msg = f"Error extracting external ideas/scope: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            return []

