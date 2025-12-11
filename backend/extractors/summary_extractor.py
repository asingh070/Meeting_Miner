"""Executive summary extractor."""
from typing import Dict
from backend.llm import get_llm_client


class SummaryExtractor:
    """Extract executive summary from meeting transcript."""
    
    SYSTEM_PROMPT = """You are an expert at analyzing meeting transcripts and creating sharp, short executive summaries.

Your task is to extract:
1. Key decisions made
2. Main outcomes and action items
3. Important discussions and context
4. Critical information that executives need to know

The transcript may contain Hinglish (Hindi-English mix) or other multilingual content. Understand and process it correctly, including phrases like "haan yaar, dekh lenge" (yes, we'll see) and other mixed-language expressions.

Create a SHARP, SHORT summary - be concise, direct, and impactful. Aim for 2-3 paragraphs maximum. Focus on what matters most."""

    def __init__(self):
        """Initialize extractor."""
        self.llm = get_llm_client()
    
    def extract(self, transcript_text: str) -> str:
        """
        Extract executive summary from transcript.
        
        Args:
            transcript_text: Full meeting transcript text
        
        Returns:
            Executive summary string
        """
        prompt = f"""Analyze the following meeting transcript and create a SHARP, SHORT executive summary.

Focus on:
- Key decisions and commitments
- Important outcomes
- Critical action items
- Significant discussions

Be direct and concise. Extract only the most important information that executives need to know.

The transcript may contain Hinglish (Hindi-English mix) or other multilingual content - process it correctly.

Transcript:
{transcript_text}

Executive Summary (keep it sharp and short):"""
        
        summary = self.llm.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.5
        )
        
        return summary.strip()



