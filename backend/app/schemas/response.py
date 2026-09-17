from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.schemas.poll import PollOptionResponse

class SubmitResponseRequest(BaseModel):
    option_id: int

class ParticipantDetail(BaseModel):
    student_id: int
    name: str
    register_number: Optional[str] = None
    email: str
    phone_number: Optional[str] = None
    option_id: Optional[int] = None
    option_text: Optional[str] = None
    submitted_at: Optional[datetime] = None

class PollRemindRequest(BaseModel):
    student_ids: Optional[List[int]] = None
    custom_message: Optional[str] = None

class MessageLogDetail(BaseModel):
    id: int
    poll_id: int
    student_id: int
    student_name: str
    recipient_phone: str
    message_type: str
    provider: str
    provider_message_id: Optional[str] = None
    delivery_status: str
    error_message: Optional[str] = None
    sent_at: datetime

class PollRemindResponse(BaseModel):
    total_targeted: int
    sent_count: int
    failed_count: int
    results: List[MessageLogDetail]

class PollParticipantsResponse(BaseModel):
    poll_id: int
    public_id: str
    creator_id: int
    question: str
    class_id: int
    class_name: str
    deadline: datetime
    is_closed: bool
    total_students: int
    completed_count: int
    pending_count: int
    completion_rate: float
    done_students: List[ParticipantDetail]
    not_done_students: List[ParticipantDetail]
    options: List[PollOptionResponse]

class StudentHistoryItem(BaseModel):
    poll_id: int
    public_id: str
    question: str
    class_name: str
    deadline: datetime
    is_closed: bool
    is_done: bool
    submitted_at: Optional[datetime] = None
    selected_option_text: Optional[str] = None

class StudentDashboardStats(BaseModel):
    active_polls_count: int
    completed_polls_count: int
    pending_polls_count: int
    completion_rate: float

class TeacherDashboardStats(BaseModel):
    my_classes_count: int
    total_students: int
    active_polls: int
    average_completion_rate: float

FacultyDashboardStats = TeacherDashboardStats
