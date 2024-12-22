from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import logging
from typing import List

from ..database.config import get_db
from .. import crud, schemas
from ..services.enhanced_ai_service import EnhancedAIService
from ..database import models

router = APIRouter(
    prefix="/meetings",
    tags=["meetings"]
)

ai_service = EnhancedAIService()
logger = logging.getLogger(__name__)

@router.post("/{meeting_id}/analyze")
async def analyze_meeting_segment(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """
    Analyze recent meeting segments and generate insights
    """
    try:
        meeting = crud.get_meeting(db, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Get recent transcripts (last 5 minutes)
        recent_transcripts = db.query(models.TranscriptSegment)\
            .filter(
                models.TranscriptSegment.meeting_id == meeting.id,
                models.TranscriptSegment.timestamp >= datetime.now(timezone.utc) - timedelta(minutes=5)
            )\
            .order_by(models.TranscriptSegment.timestamp.asc())\
            .all()

        if not recent_transcripts:
            return {"message": "No recent transcripts to analyze"}

        transcript_texts = [t.text for t in recent_transcripts]
        
        # Generate insights using AI service
        summary = await ai_service.generate_progressive_summary(transcript_texts)
        if summary:
            summary_schema = schemas.SummaryCreate(
                summary_text=summary.get('summary', ''),
                summary_type='progressive',
                key_points=summary.get('topics'),
                decisions=summary.get('decisions')
            )
            crud.add_summary(db, meeting_id, summary_schema)

        # Generate follow-up questions
        questions = await ai_service.generate_followup_questions(' '.join(transcript_texts))
        if questions:
            for question in questions:
                question_schema = schemas.FollowUpQuestionCreate(
                    question_text=question,
                    context=' '.join(transcript_texts[-2:])
                )
                crud.add_follow_up_question(db, meeting_id, question_schema)

        # Extract action items
        action_items = await ai_service.extract_action_items(' '.join(transcript_texts))
        if action_items:
            for item in action_items:
                action_schema = schemas.ActionItemCreate(
                    description=item['description'],
                    assigned_to=item.get('assigned_to'),
                    due_date=item.get('due_date'),
                    priority=item.get('priority', 'medium')
                )
                crud.add_action_item(db, meeting_id, action_schema)

        return {
            "summary": summary,
            "questions": questions,
            "action_items": action_items
        }

    except Exception as e:
        logger.error(f"Error analyzing meeting segment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{meeting_id}/finalize")
async def finalize_meeting(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """
    Generate final meeting summary and insights
    """
    try:
        meeting = crud.get_meeting(db, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        transcripts = db.query(models.TranscriptSegment)\
            .filter(models.TranscriptSegment.meeting_id == meeting.id)\
            .order_by(models.TranscriptSegment.timestamp.asc())\
            .all()

        if not transcripts:
            raise HTTPException(status_code=400, detail="No transcripts found")

        full_transcript = ' '.join([t.text for t in transcripts])

        # Generate final summary
        final_summary = await ai_service.generate_final_summary(full_transcript)
        if final_summary:
            summary_schema = schemas.SummaryCreate(
                summary_text=final_summary['executive_summary'],
                summary_type='final',
                key_points=final_summary['discussion_points'],
                decisions=final_summary['decisions']
            )
            crud.add_summary(db, meeting_id, summary_schema)

        # Identify topics
        topics = await ai_service.identify_topics(full_transcript)
        if topics:
            for topic in topics:
                topic_schema = schemas.TopicCreate(
                    name=topic['topic'],
                    description=topic['description'],
                    time_spent=topic['time_spent'],
                    participants=topic['participants']
                )
                crud.add_topic(db, meeting_id, topic_schema)

        # Mark meeting as inactive
        meeting.is_active = False
        meeting.end_time = datetime.now(timezone.utc)
        db.commit()

        return {
            "summary": final_summary,
            "topics": topics,
            "status": "meeting_finalized"
        }

    except Exception as e:
        logger.error(f"Error finalizing meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{meeting_id}/insights")
async def get_meeting_insights(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all insights for a meeting
    """
    try:
        meeting = crud.get_meeting(db, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        progressive_summaries = crud.get_progressive_summaries(db, meeting_id)
        final_summary = crud.get_final_summary(db, meeting_id)
        topics = crud.get_meeting_topics(db, meeting_id)
        questions = crud.get_unanswered_questions(db, meeting_id)

        return {
            "progressive_summaries": [
                {
                    "summary": s.summary_text,
                    "key_points": s.key_points,
                    "decisions": s.decisions,
                    "created_at": s.created_at
                } for s in progressive_summaries
            ],
            "final_summary": {
                "summary": final_summary.summary_text,
                "key_points": final_summary.key_points,
                "decisions": final_summary.decisions,
                "created_at": final_summary.created_at
            } if final_summary else None,
            "topics": [
                {
                    "name": t.name,
                    "description": t.description,
                    "time_spent": t.time_spent,
                    "participants": t.participants
                } for t in topics
            ],
            "unanswered_questions": [
                {
                    "question": q.question_text,
                    "context": q.context,
                    "created_at": q.created_at
                } for q in questions
            ]
        }

    except Exception as e:
        logger.error(f"Error getting meeting insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))