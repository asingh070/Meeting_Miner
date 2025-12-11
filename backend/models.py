"""Database models for MeetingMiner."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Meeting(Base):
    """Meeting transcript model."""
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=True)
    project_name = Column(String(500), nullable=True)  # Main project name extracted from transcript
    transcript_text = Column(Text, nullable=True)
    transcript_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    extracted_data = relationship("ExtractedData", back_populates="meeting", uselist=False, cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="meeting", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="meeting", cascade="all, delete-orphan")


class ExtractedData(Base):
    """Extracted intelligence from meetings."""
    __tablename__ = "extracted_data"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), unique=True, nullable=False)
    summary = Column(Text, nullable=True)
    project_details_json = Column(JSON, nullable=True)  # Explicit project candidates with details
    health_signals_json = Column(JSON, nullable=True)
    pulse_json = Column(JSON, nullable=True)
    pain_points_json = Column(JSON, nullable=True)
    ideas_scope_json = Column(JSON, nullable=True)  # External ideas and scope
    overall_sentiment = Column(String(50), nullable=True)  # positive, neutral, negative
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="extracted_data")


class Project(Base):
    """Project extracted from meetings."""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    owner = Column(String(200), nullable=True)
    status = Column(String(50), nullable=True)  # e.g., "proposed", "in_progress", "blocked"
    blockers = Column(JSON, nullable=True)  # List of blockers
    risks = Column(JSON, nullable=True)  # List of risks
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="projects")


class ChatHistory(Base):
    """Chat history for meeting queries."""
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True)  # None for cross-meeting queries
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="chat_history")


