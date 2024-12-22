from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .config import Base

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(String, unique=True, index=True)
    title = Column(String, nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow, index=True)
    end_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    transcripts = relationship(
        "TranscriptSegment",
        back_populates="meeting",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="TranscriptSegment.timestamp.asc()"
    )
    
    action_items = relationship(
        "ActionItem",
        back_populates="meeting",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ActionItem.created_at.desc()"
    )
    
    summaries = relationship(
        "Summary",
        back_populates="meeting",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Summary.created_at.desc()"
    )
    
    follow_up_questions = relationship(
        "FollowUpQuestion",
        back_populates="meeting",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="FollowUpQuestion.created_at.desc()"
    )

    topics = relationship(
        "Topic",
        back_populates="meeting",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Topic.created_at.desc()"
    )

    def __repr__(self):
        return f"<Meeting(id={self.id}, meeting_id={self.meeting_id})>"

class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"))
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    speaker = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    audio_type = Column(String, nullable=False, default="microphone", index=True)
    
    meeting = relationship("Meeting", back_populates="transcripts")
    
    def __repr__(self):
        return f"<TranscriptSegment(id={self.id}, audio_type={self.audio_type}, text={self.text[:30]}...)>"

class ActionItem(Base):
    __tablename__ = "action_items"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"))
    description = Column(Text, nullable=False)
    assigned_to = Column(String, nullable=True)
    due_date = Column(DateTime, nullable=True)
    status = Column(String, default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    priority = Column(String, nullable=True)  # Added priority field
    
    meeting = relationship("Meeting", back_populates="action_items")
    
    def __repr__(self):
        return f"<ActionItem(id={self.id}, status={self.status})>"

class Summary(Base):
    __tablename__ = "summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"))
    summary_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    summary_type = Column(String, nullable=False, default='progressive')  # 'progressive' or 'final'
    key_points = Column(Text, nullable=True)  # Added for structured key points
    decisions = Column(Text, nullable=True)   # Added for tracking decisions
    
    meeting = relationship("Meeting", back_populates="summaries")
    
    def __repr__(self):
        return f"<Summary(id={self.id}, type={self.summary_type})>"

class FollowUpQuestion(Base):
    __tablename__ = "follow_up_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"))
    question_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    context = Column(Text, nullable=True)  # Added to store context that triggered the question
    answered = Column(Boolean, default=False)  # Added to track if question was addressed
    
    meeting = relationship("Meeting", back_populates="follow_up_questions")
    
    def __repr__(self):
        return f"<FollowUpQuestion(id={self.id})>"

class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    time_spent = Column(String, nullable=True)  # Approximate time spent on topic
    participants = Column(Text, nullable=True)  # Key participants in the topic
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    meeting = relationship("Meeting", back_populates="topics")
    
    def __repr__(self):
        return f"<Topic(id={self.id}, name={self.name})>"