"""Project candidate extractor."""
from typing import Dict, List, Optional
from backend.llm import get_llm_client
from backend.logger import logger


class ProjectExtractor:
    """Extract project details for the MAIN project from meeting transcript."""
    
    SYSTEM_PROMPT = """You are an expert at extracting detailed information about the MAIN project being discussed in a meeting.

Your task is to extract detailed information ONLY about the PRIMARY/MAIN project that this meeting is about.
DO NOT extract information about other projects that are mentioned in passing or discussed briefly.
Focus ONLY on the main project that this transcript is specifically about.

Extract:
1. Project name (should match the main project)
2. Detailed description of what this project involves
3. Owner or person responsible (if mentioned)
4. Current status: Proposed, In Progress, Blocked, or Completed (capitalize first letter)
5. Timeline hints or deadlines mentioned
6. Any side-chats or brief mentions related to THIS main project

The transcript may contain Hinglish (Hindi-English mix) or other multilingual content. Understand phrases like "haan yaar, dekh lenge" (yes, we'll see) which might indicate tentative commitments.

IMPORTANT: Only extract details about the MAIN project. Ignore other projects that are mentioned but are not the focus of this meeting.

Return a JSON array with ONE project object (the main project) with the following structure:
[
  {
    "name": "Main project name",
    "description": "Detailed description of the main project",
    "owner": "Person responsible (if mentioned)",
    "status": "Proposed|In Progress|Blocked|Completed",
    "timeline_hints": "Any timeline information mentioned"
  }
]

If the main project cannot be clearly identified, return an empty array []."""

    def __init__(self):
        """Initialize extractor."""
        self.llm = get_llm_client()
    
    def extract(self, transcript_text: str, main_project_name: Optional[str] = None) -> List[Dict]:
        """
        Extract project candidates from transcript.
        
        Args:
            transcript_text: Full meeting transcript text
            main_project_name: Optional main project name (for reference, but extract all projects)
        
        Returns:
            List of project dictionaries
        """
        prompt = f"""Analyze the following meeting transcript and identify all project candidates.

Look for:
- Explicit project mentions
- Implicit projects from discussions
- Side conversations that might indicate projects
- Any work items or initiatives discussed

Be thorough - even brief mentions or side-chats can be important projects.

Transcript:
{transcript_text}

Return a JSON array of projects. If no projects are found, return an empty array []."""

        try:
            result = self.llm.generate_json(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.3
            )
            
            # Handle different response formats
            if isinstance(result, dict):
                if "projects" in result:
                    projects = result["projects"]
                elif "data" in result:
                    projects = result["data"]
                else:
                    projects = [result]
            elif isinstance(result, list):
                projects = result
            else:
                projects = []
            
            # Ensure all projects have required fields and capitalize status
            normalized_projects = []
            for project in projects:
                if isinstance(project, dict):
                    status = project.get("status", "proposed")
                    # Capitalize status properly
                    status = status.strip()
                    if status:
                        # Handle different formats: "in_progress" -> "In Progress", "proposed" -> "Proposed"
                        status_lower = status.lower().replace("_", " ")
                        if status_lower == "in progress":
                            status = "In Progress"
                        elif status_lower == "in_progress":
                            status = "In Progress"
                        elif status_lower == "proposed":
                            status = "Proposed"
                        elif status_lower == "blocked":
                            status = "Blocked"
                        elif status_lower == "completed":
                            status = "Completed"
                        else:
                            # Capitalize first letter of each word
                            status = " ".join(word.capitalize() for word in status_lower.split())
                    
                    normalized_projects.append({
                        "name": project.get("name", "Unnamed Project"),
                        "description": project.get("description", ""),
                        "owner": project.get("owner", ""),
                        "status": status,
                        "timeline_hints": project.get("timeline_hints", "")
                    })
            
            return normalized_projects
        except Exception as e:
            # Fallback to empty list on error
            error_msg = f"Error extracting projects: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            return []


