from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Dict, Optional, List
import uuid
import logging

from ..database.models import Meeting, TranscriptSegment, ActionItem, Summary, FollowUpQuestion
from ..database.schemas import (
    ActionItemBase,
    SummaryBase,
    FollowUpQuestionBase
)

logger = logging.getLogger(__name__)

class MeetingManager:
    def __init__(self):
        self.active_meetings: Dict[str, int] = {}  # client_id -> meeting_id
        
    async def start_meeting(self, db: Session, client_id: str, title: Optional[str] = None) -> Meeting:
        """Start a new meeting and associate it with a client"""
        try:
            meeting = Meeting(
                meeting_id=str(uuid.uuid4()),
                title=title or f"Meeting {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
                start_time=datetime.now(timezone.utc),
                is_active=True
            )
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
            
            self.active_meetings[client_id] = meeting.id
            logger.info(f"Started meeting {meeting.id} for client {client_id}")
            return meeting
        except Exception as e:
            logger.error(f"Error starting meeting: {e}")
            db.rollback()
            raise
    
    async def end_meeting(self, db: Session, client_id: str) -> Optional[Meeting]:
        """End an active meeting"""
        try:
            meeting_id = self.active_meetings.get(client_id)
            if meeting_id:
                meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
                if meeting:
                    meeting.end_time = datetime.now(timezone.utc)
                    meeting.is_active = False
                    db.commit()
                    db.refresh(meeting)
                    del self.active_meetings[client_id]
                    logger.info(f"Ended meeting {meeting_id} for client {client_id}")
                    return meeting
            return None
        except Exception as e:
            logger.error(f"Error ending meeting: {e}")
            db.rollback()
            raise
    
    async def add_transcript_segment(
        self, 
        db: Session, 
        client_id: str, 
        text: str, 
        is_final: bool,
        speaker: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> Optional[TranscriptSegment]:
        """Add a transcript segment to the active meeting"""
        try:
            meeting_id = self.active_meetings.get(client_id)
            if meeting_id and is_final:
                segment = TranscriptSegment(
                    meeting_id=meeting_id,
                    text=text,
                    timestamp=datetime.now(timezone.utc),
                    speaker=speaker,
                    confidence=confidence
                )
                db.add(segment)
                db.commit()
                db.refresh(segment)
                return segment
            return None
        except Exception as e:
            logger.error(f"Error adding transcript segment: {e}")
            db.rollback()
            raise

    async def add_action_item(
        self, 
        db: Session, 
        client_id: str, 
        action_item: ActionItemBase
    ) -> Optional[ActionItem]:
        """Add an action item to the active meeting"""
        try:
            meeting_id = self.active_meetings.get(client_id)
            if meeting_id:
                db_action_item = ActionItem(
                    meeting_id=meeting_id,
                    description=action_item.description,
                    assigned_to=action_item.assigned_to,
                    due_date=action_item.due_date,
                    status="pending",
                    created_at=datetime.now(timezone.utc)
                )
                db.add(db_action_item)
                db.commit()
                db.refresh(db_action_item)
                return db_action_item
            return None
        except Exception as e:
            logger.error(f"Error adding action item: {e}")
            db.rollback()
            raise

    async def add_follow_up_question(
        self, 
        db: Session, 
        client_id: str, 
        question: FollowUpQuestionBase
    ) -> Optional[FollowUpQuestion]:
        """Add a follow-up question to the active meeting"""
        try:
            meeting_id = self.active_meetings.get(client_id)
            if meeting_id:
                db_question = FollowUpQuestion(
                    meeting_id=meeting_id,
                    question_text=question.question_text,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(db_question)
                db.commit()
                db.refresh(db_question)
                return db_question
            return None
        except Exception as e:
            logger.error(f"Error adding follow-up question: {e}")
            db.rollback()
            raise

    async def add_summary(
        self, 
        db: Session, 
        client_id: str, 
        summary: SummaryBase
    ) -> Optional[Summary]:
        """Add a summary to the active meeting"""
        try:
            meeting_id = self.active_meetings.get(client_id)
            if meeting_id:
                db_summary = Summary(
                    meeting_id=meeting_id,
                    summary_text=summary.summary_text,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(db_summary)
                db.commit()
                db.refresh(db_summary)
                return db_summary
            return None
        except Exception as e:
            logger.error(f"Error adding summary: {e}")
            db.rollback()
            raise

    def get_active_meeting_id(self, client_id: str) -> Optional[int]:
        """Get the active meeting ID for a client"""
        return self.active_meetings.get(client_id)

    def is_meeting_active(self, client_id: str) -> bool:
        """Check if a client has an active meeting"""
        return client_id in self.active_meetings