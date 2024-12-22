from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime
from typing import List, Optional

def create_meeting(db: Session, meeting: schemas.MeetingCreate):
    db_meeting = models.Meeting(**meeting.dict())
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

def get_meeting(db: Session, meeting_id: str):
    return db.query(models.Meeting).filter(models.Meeting.meeting_id == meeting_id).first()

def add_action_item(db: Session, meeting_id: str, action_item: schemas.ActionItemCreate):
    meeting = get_meeting(db, meeting_id)
    if meeting:
        db_action_item = models.ActionItem(**action_item.dict(), meeting_id=meeting.id)
        db.add(db_action_item)
        db.commit()
        db.refresh(db_action_item)
        return db_action_item
    return None

def add_transcript_segment(
    db: Session, 
    meeting_id: str, 
    text: str, 
    speaker: Optional[str] = None,
    confidence: Optional[float] = None,
    audio_type: str = "microphone"
):
    meeting = get_meeting(db, meeting_id)
    if meeting:
        segment = models.TranscriptSegment(
            meeting_id=meeting.id,
            text=text,
            speaker=speaker,
            confidence=confidence,
            audio_type=audio_type,
            timestamp=datetime.utcnow()
        )
        db.add(segment)
        db.commit()
        db.refresh(segment)
        return segment
    return None

def add_summary(
    db: Session, 
    meeting_id: str, 
    summary: schemas.SummaryCreate
):
    meeting = get_meeting(db, meeting_id)
    if meeting:
        db_summary = models.Summary(**summary.dict(), meeting_id=meeting.id)
        db.add(db_summary)
        db.commit()
        db.refresh(db_summary)
        return db_summary
    return None

def add_follow_up_question(
    db: Session,
    meeting_id: str,
    question: schemas.FollowUpQuestionCreate
):
    meeting = get_meeting(db, meeting_id)
    if meeting:
        db_question = models.FollowUpQuestion(**question.dict(), meeting_id=meeting.id)
        db.add(db_question)
        db.commit()
        db.refresh(db_question)
        return db_question
    return None

def add_topic(
    db: Session,
    meeting_id: str,
    topic: schemas.TopicCreate
):
    meeting = get_meeting(db, meeting_id)
    if meeting:
        db_topic = models.Topic(**topic.dict(), meeting_id=meeting.id)
        db.add(db_topic)
        db.commit()
        db.refresh(db_topic)
        return db_topic
    return None

def get_meeting_topics(db: Session, meeting_id: str) -> List[models.Topic]:
    meeting = get_meeting(db, meeting_id)
    if meeting:
        return db.query(models.Topic)\
            .filter(models.Topic.meeting_id == meeting.id)\
            .order_by(models.Topic.created_at.desc())\
            .all()
    return []

def update_follow_up_question_status(
    db: Session,
    question_id: int,
    answered: bool
):
    question = db.query(models.FollowUpQuestion).filter(models.FollowUpQuestion.id == question_id).first()
    if question:
        question.answered = answered
        db.commit()
        db.refresh(question)
        return question
    return None

def get_unanswered_questions(db: Session, meeting_id: str) -> List[models.FollowUpQuestion]:
    meeting = get_meeting(db, meeting_id)
    if meeting:
        return db.query(models.FollowUpQuestion)\
            .filter(
                models.FollowUpQuestion.meeting_id == meeting.id,
                models.FollowUpQuestion.answered == False
            )\
            .order_by(models.FollowUpQuestion.created_at.desc())\
            .all()
    return []

def get_progressive_summaries(db: Session, meeting_id: str) -> List[models.Summary]:
    meeting = get_meeting(db, meeting_id)
    if meeting:
        return db.query(models.Summary)\
            .filter(
                models.Summary.meeting_id == meeting.id,
                models.Summary.summary_type == 'progressive'
            )\
            .order_by(models.Summary.created_at.desc())\
            .all()
    return []

def get_final_summary(db: Session, meeting_id: str) -> Optional[models.Summary]:
    meeting = get_meeting(db, meeting_id)
    if meeting:
        return db.query(models.Summary)\
            .filter(
                models.Summary.meeting_id == meeting.id,
                models.Summary.summary_type == 'final'
            )\
            .order_by(models.Summary.created_at.desc())\
            .first()
    return None