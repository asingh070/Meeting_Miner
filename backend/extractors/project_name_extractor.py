"""Main project name extractor from meeting transcript."""
from typing import Optional
from backend.llm import get_llm_client
from backend.logger import logger


class ProjectNameExtractor:
    """Extract the main project name from meeting transcript."""
    
    SYSTEM_PROMPT = """You are an expert at identifying the main project or initiative being discussed in a meeting transcript.

Your task is to identify:
1. The primary project or initiative name that this meeting is about
2. Extract the project name directly from the transcript content
3. If multiple projects are discussed, identify the MAIN or PRIMARY project
4. If you are unsure or cannot clearly identify a project name from the transcript, return "UNSURE" (exactly this word)

The transcript may contain Hinglish (Hindi-English mix) or other multilingual content. Understand and process it correctly.

Return ONLY the project name as a string. Be concise - typically 2-5 words maximum.
Examples: "Mobile App Launch", "Q4 Roadmap Planning", "API Integration Project", "Customer Portal Redesign".
If unsure, return exactly "UNSURE"."""

    def __init__(self):
        """Initialize extractor."""
        self.llm = get_llm_client()
    
    def extract(self, transcript_text: str, meeting_title: Optional[str] = None) -> str:
        """
        Extract main project name from transcript.
        
        Args:
            transcript_text: Full meeting transcript text
            meeting_title: Optional meeting title to use as fallback
        
        Returns:
            Project name string (or meeting title if extraction is unsure)
        """
        title_context = ""
        if meeting_title:
            title_context = f"\n\nMeeting Title: {meeting_title}\n(If you are unsure about the project name from the transcript, return 'UNSURE' and the title will be used as fallback)"
        
        prompt = f"""Analyze the following meeting transcript and identify the MAIN project or initiative name that this meeting is about.

Extract the project name directly from the transcript content itself.
Look for:
- Project names explicitly mentioned in the transcript
- Primary project being discussed
- Main initiative or work item mentioned in conversations
- If multiple projects, identify the PRIMARY one

Be concise - return only the project name (2-5 words typically).
If you are unsure or cannot clearly identify a project name from the transcript, return exactly "UNSURE".

{title_context}

Transcript:
{transcript_text}

Main Project Name:"""

        try:
            result = self.llm.generate(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=50
            )
            
            # Clean up the result
            project_name = result.strip()
            # Remove quotes if present
            project_name = project_name.strip('"').strip("'")
            # Limit length
            if len(project_name) > 100:
                project_name = project_name[:100]
            
            # Check if LLM returned "UNSURE" or if result is empty/unclear
            if not project_name or project_name.upper() == "UNSURE" or project_name.lower() in ["unsure", "unknown", "unnamed project", "general discussion"]:
                # Use meeting title as fallback
                if meeting_title and meeting_title.strip():
                    logger.info(f"Project name extraction was unsure, using meeting title as fallback: {meeting_title}")
                    return meeting_title.strip()[:100]  # Limit to 100 chars
                else:
                    return "Unnamed Project"
            
            return project_name
        except Exception as e:
            error_msg = f"Error extracting project name: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            # Fallback to meeting title or default
            if meeting_title and meeting_title.strip():
                logger.info(f"Error in extraction, using meeting title as fallback: {meeting_title}")
                return meeting_title.strip()[:100]
            return "Unnamed Project"

