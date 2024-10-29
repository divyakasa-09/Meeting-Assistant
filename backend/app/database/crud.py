from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime

def create_meeting(db: Session, meeting: schemas.MeetingCreate):
    db_meeting = models.Meeting(**meeting.dict())
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

def get_meeting(db: Session, meeting_id: str):
    return db.query(models.Meeting).filter(models.Meeting.meeting_id == meeting_id).first()

def update_meeting_transcript(db: Session, meeting_id: str, transcript: str):
    meeting = get_meeting(db, meeting_id)
    if meeting:
        meeting.full_transcript = transcript
        db.commit()
        return meeting
    return None

def add_action_item(db: Session, meeting_id: str, action_item: schemas.ActionItemCreate):
    meeting = get_meeting(db, meeting_id)
    if meeting:
        db_action_item = models.ActionItem(**action_item.dict(), meeting_id=meeting.id)
        db.add(db_action_item)
        db.commit()
        db.refresh(db_action_item)
        return db_action_item
    return None

def add_transcript_segment(db: Session, meeting_id: str, text: str, speaker: str = None):
    meeting = get_meeting(db, meeting_id)
    if meeting:
        segment = models.TranscriptSegment(
            meeting_id=meeting.id,
            text=text,
            speaker=speaker,
            timestamp=datetime.utcnow()
        )
        db.add(segment)
        db.commit()
        db.refresh(segment)
        return segment
    return None