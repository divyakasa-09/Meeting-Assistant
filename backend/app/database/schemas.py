from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# ActionItem schemas with new priority field
class ActionItemBase(BaseModel):
    description: str
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str = "pending"
    priority: Optional[str] = None  # New field

class ActionItemCreate(ActionItemBase):
    pass

class ActionItem(ActionItemBase):
    id: int
    meeting_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# TranscriptSegment schemas (unchanged)
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

# Summary schemas with new fields
class SummaryBase(BaseModel):
    summary_text: str
    summary_type: str = "progressive"  # New field
    key_points: Optional[str] = None   # New field
    decisions: Optional[str] = None    # New field

class SummaryCreate(SummaryBase):
    pass

class Summary(SummaryBase):
    id: int
    meeting_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# FollowUpQuestion schemas with new fields
class FollowUpQuestionBase(BaseModel):
    question_text: str
    context: Optional[str] = None    # New field
    answered: bool = False           # New field

class FollowUpQuestionCreate(FollowUpQuestionBase):
    pass

class FollowUpQuestion(FollowUpQuestionBase):
    id: int
    meeting_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# New Topic schemas
class TopicBase(BaseModel):
    name: str
    description: Optional[str] = None
    time_spent: Optional[str] = None
    participants: Optional[str] = None

class TopicCreate(TopicBase):
    pass

class Topic(TopicBase):
    id: int
    meeting_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Meeting schemas with topics added
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
    topics: List[Topic] = []  # New field

    class Config:
        from_attributes = True