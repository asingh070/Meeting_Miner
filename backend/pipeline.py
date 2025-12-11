"""Main processing pipeline for meeting transcripts."""
import json
import traceback
from typing import Dict, Optional
from backend.transcript_parser import TranscriptParser
from backend.extractors import (
    SummaryExtractor,
    ProjectNameExtractor,
    ProjectExtractor,
    HealthExtractor,
    PulseExtractor,
    PainPointsExtractor,
    ExternalIdeasScopeExtractor
)
from backend.embeddings import EmbeddingStore
from backend.database import get_db_session
from backend.models import Meeting, ExtractedData, Project
from backend.logger import logger


class MeetingPipeline:
    """End-to-end pipeline for processing meeting transcripts."""
    
    def __init__(self):
        """Initialize pipeline."""
        self.parser = TranscriptParser()
        self.summary_extractor = SummaryExtractor()
        self.project_name_extractor = ProjectNameExtractor()
        self.project_extractor = ProjectExtractor()
        self.health_extractor = HealthExtractor()
        self.pulse_extractor = PulseExtractor()
        self.pain_points_extractor = PainPointsExtractor()
        self.external_ideas_scope_extractor = ExternalIdeasScopeExtractor()
        self.embedding_store = EmbeddingStore()
    
    def process(self, transcript: str, title: Optional[str] = None, project_name: Optional[str] = None, transcript_json: Optional[Dict] = None) -> Dict:
        """
        Process a meeting transcript end-to-end.
        
        Args:
            transcript: Transcript text (plain text or JSON string)
            title: Optional meeting title
            transcript_json: Optional pre-parsed JSON transcript
        
        Returns:
            Dictionary with meeting ID and extracted data
        """
        # Parse transcript
        # If transcript_json is provided, use it directly; otherwise parse the transcript string
        if transcript_json and isinstance(transcript_json, dict):
            # Use provided JSON directly (parse method accepts dict)
            parsed = self.parser.parse(transcript_json)
        else:
            # Parse from transcript string
            parsed = self.parser.parse(transcript)
        
        transcript_text = self.parser.get_full_text(parsed)
        speakers = self.parser.get_speakers(parsed)
        
        # Extract title and meeting_id from parsed JSON if present
        extracted_title = self.parser.get_title(parsed)
        extracted_meeting_id = self.parser.get_meeting_id(parsed)
        
        # Use extracted title if no title was provided
        if not title and extracted_title:
            title = extracted_title
            logger.info(f"Using title from JSON: {title}")
        
        # Log extracted meeting_id if present (for reference, not stored as DB field)
        if extracted_meeting_id:
            logger.info(f"Found meeting_id in JSON: {extracted_meeting_id}")
        
        # Store meeting in database
        db = get_db_session()
        try:
            # Use user-provided project name if available, otherwise extract it (use title as fallback)
            if not project_name or not project_name.strip():
                project_name = self.project_name_extractor.extract(transcript_text, meeting_title=title)
            else:
                project_name = project_name.strip()
                logger.info(f"Using user-provided project name: {project_name}")
            
            # Store the parsed JSON (which includes meeting_id if present)
            meeting = Meeting(
                title=title,
                project_name=project_name,
                transcript_text=transcript_text,
                transcript_json=parsed
            )
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
            meeting_id = meeting.id
            
            # Run extractors
            summary = self.summary_extractor.extract(transcript_text)
            # Include project name in summary
            if project_name and project_name != "Unnamed Project":
                summary = f"**Project: {project_name}**\n\n{summary}"
            
            # Extract project details for the MAIN project only
            project_details = self.project_extractor.extract(transcript_text, main_project_name=project_name)
            # Extract health signals for the MAIN project only
            health_signals = self.health_extractor.extract(transcript_text, main_project_name=project_name)
            pulse = self.pulse_extractor.extract(transcript_text, speakers)
            # Extract pain points for the MAIN project only
            pain_points = self.pain_points_extractor.extract(transcript_text, main_project_name=project_name)
            external_ideas_scope = self.external_ideas_scope_extractor.extract(transcript_text)  # External ideas/scope
            
            # Extract overall sentiment from pulse
            overall_sentiment = pulse.get("overall_sentiment", "neutral") if pulse else "neutral"
            
            # Check if extracted_data already exists for this meeting
            existing_extracted_data = db.query(ExtractedData).filter(ExtractedData.meeting_id == meeting_id).first()
            
            if existing_extracted_data:
                # Update existing extracted data
                existing_extracted_data.summary = summary
                existing_extracted_data.project_details_json = project_details
                existing_extracted_data.health_signals_json = health_signals
                existing_extracted_data.pulse_json = pulse
                existing_extracted_data.pain_points_json = pain_points
                existing_extracted_data.ideas_scope_json = external_ideas_scope
                existing_extracted_data.overall_sentiment = overall_sentiment
                logger.info(f"Updated existing extracted_data for meeting {meeting_id}")
            else:
                # Create new extracted data
                extracted_data = ExtractedData(
                    meeting_id=meeting_id,
                    summary=summary,
                    project_details_json=project_details,
                    health_signals_json=health_signals,
                    pulse_json=pulse,
                    pain_points_json=pain_points,
                    ideas_scope_json=external_ideas_scope,
                    overall_sentiment=overall_sentiment
                )
                db.add(extracted_data)
                logger.info(f"Created new extracted_data for meeting {meeting_id}")
            
            # Delete existing projects for this meeting before adding new ones (to avoid duplicates on reprocessing)
            db.query(Project).filter(Project.meeting_id == meeting_id).delete()
            
            # Store project details as separate entities
            for project_data in project_details:
                # Ensure status is capitalized
                status = project_data.get("status", "Proposed")
                if status:
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
                
                project = Project(
                    meeting_id=meeting_id,
                    name=project_data.get("name", "Unnamed Project"),
                    description=project_data.get("description", ""),
                    owner=project_data.get("owner", ""),
                    status=status,
                    blockers=health_signals.get("blockers", []),
                    risks=health_signals.get("risks", [])
                )
                db.add(project)
            
            db.commit()
            
            # Add to vector store for RAG
            self.embedding_store.add_meeting(meeting_id, transcript_text)
            
            return {
                "meeting_id": meeting_id,
                "project_name": project_name,
                "summary": summary,
                "project_details": project_details,
                "health_signals": health_signals,
                "pulse": pulse,
                "pain_points": pain_points,
                "external_ideas_scope": external_ideas_scope,
                "overall_sentiment": overall_sentiment
            }
        except Exception as e:
            db.rollback()
            error_msg = f"Error processing meeting: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            raise Exception(error_msg)
        finally:
            db.close()
    
    def get_meeting(self, meeting_id: int) -> Optional[Dict]:
        """
        Retrieve processed meeting data.
        
        Args:
            meeting_id: Meeting ID
        
        Returns:
            Dictionary with meeting data or None
        """
        db = get_db_session()
        try:
            meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
            if not meeting:
                return None
            
            extracted_data = db.query(ExtractedData).filter(ExtractedData.meeting_id == meeting_id).first()
            projects = db.query(Project).filter(Project.meeting_id == meeting_id).all()
            
            # Get project_details from JSON or from projects table
            project_details = extracted_data.project_details_json if extracted_data and extracted_data.project_details_json else []
            # Fallback to projects table if project_details_json is empty
            if not project_details and projects:
                project_details = [
                    {
                        "name": p.name,
                        "description": p.description,
                        "owner": p.owner,
                        "status": p.status,
                        "blockers": p.blockers,
                        "risks": p.risks
                    }
                    for p in projects
                ]
            
            return {
                "id": meeting.id,
                "title": meeting.title,
                "project_name": meeting.project_name,
                "created_at": meeting.created_at.isoformat() if meeting.created_at else None,
                "summary": extracted_data.summary if extracted_data else None,
                "project_details": project_details,
                "projects": project_details,  # Keep for backward compatibility
                "health_signals": extracted_data.health_signals_json if extracted_data else {},
                "pulse": extracted_data.pulse_json if extracted_data else {},
                "pain_points": extracted_data.pain_points_json if extracted_data else {},
                "external_ideas_scope": extracted_data.ideas_scope_json if extracted_data else [],
                "ideas_proposals": extracted_data.ideas_scope_json if extracted_data else [],  # Backward compatibility
                "overall_sentiment": extracted_data.overall_sentiment if extracted_data else "neutral"
            }
        except Exception as e:
            error_msg = f"Error retrieving meeting {meeting_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            raise
        finally:
            db.close()
    
    def list_meetings(self) -> list:
        """
        List all meetings.
        
        Returns:
            List of meeting dictionaries
        """
        db = get_db_session()
        try:
            meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).all()
            return [
                {
                    "id": m.id,
                    "title": m.title,
                    "project_name": m.project_name,
                    "created_at": m.created_at.isoformat() if m.created_at else None
                }
                for m in meetings
            ]
        except Exception as e:
            error_msg = f"Error listing meetings: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            raise
        finally:
            db.close()


