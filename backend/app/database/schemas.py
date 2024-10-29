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
        orm_mode = True

class MeetingBase(BaseModel):
    title: Optional[str] = None
    meeting_id: str

class MeetingCreate(MeetingBase):
    pass

class Meeting(MeetingBase):
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    summary: Optional[str] = None
    action_items: List[ActionItem] = []
    is_active: bool

    class Config:
        orm_mode = True