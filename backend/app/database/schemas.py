from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ActionItemBase(BaseModel):
    description: str
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str = "pending"

class ActionItemCreate(ActionItemBase):
    pass

class ActionItem(ActionItemBase):
    id: int
    meeting_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TranscriptSegmentBase(BaseModel):
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None

class TranscriptSegmentCreate(TranscriptSegmentBase):
    pass

class TranscriptSegment(TranscriptSegmentBase):
    id: int
    meeting_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class SummaryBase(BaseModel):
    summary_text: str

class SummaryCreate(SummaryBase):
    pass

class Summary(SummaryBase):
    id: int
    meeting_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class FollowUpQuestionBase(BaseModel):
    question_text: str

class FollowUpQuestionCreate(FollowUpQuestionBase):
    pass

class FollowUpQuestion(FollowUpQuestionBase):
    id: int
    meeting_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MeetingBase(BaseModel):
    title: Optional[str] = None
    meeting_id: str

class MeetingCreate(MeetingBase):
    pass

class Meeting(MeetingBase):
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    is_active: bool
    transcripts: List[TranscriptSegment] = []
    summaries: List[Summary] = []
    action_items: List[ActionItem] = []
    follow_up_questions: List[FollowUpQuestion] = []

    class Config:
        from_attributes = True