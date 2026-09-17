from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.models.enums import PollStatus

class PollOptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    option_text: str
    position: int
    votes_count: int = 0
    percentage: float = 0.0

class PollCreate(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    options: List[str] = Field(..., min_length=2, max_length=10)
    deadline: datetime
    allow_response_editing: bool = False

    @model_validator(mode='after')
    def validate_options(self):
        non_empty = [opt.strip() for opt in self.options if opt.strip()]
        if len(non_empty) < 2:
            raise ValueError("At least 2 distinct non-empty options are required.")
        return self

class PollUpdate(BaseModel):
    question: Optional[str] = None
    deadline: Optional[datetime] = None
    status: Optional[PollStatus] = None
    allow_response_editing: Optional[bool] = None

class PollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: str
    class_id: int
    class_name: str
    creator_id: int
    creator_name: str
    question: str
    deadline: datetime
    status: PollStatus
    allow_response_editing: bool
    created_at: datetime
    options: List[PollOptionResponse] = []
    has_responded: bool = False
    selected_option_id: Optional[int] = None
    total_students: int = 0
    total_responses: int = 0
    completion_rate: float = 0.0
    is_closed: bool = False
    share_url: str = ""
    whatsapp_share_url: str = ""
