from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class ClassCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100) # e.g. "AIDS-A"
    department: str = Field(..., min_length=2, max_length=100)
    year: int = Field(..., ge=1, le=5)
    section: str = Field(..., min_length=1, max_length=10)
    academic_year: str = Field(default="2026-27", max_length=20)
    allow_rep_poll_creation: bool = False

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    year: Optional[int] = None
    section: Optional[str] = None
    academic_year: Optional[str] = None
    is_active: Optional[bool] = None
    allow_rep_poll_creation: Optional[bool] = None

class ClassTeacherDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    teacher_id: int
    name: str
    email: str
    employee_id: Optional[str] = None

class ClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    department: str
    year: int
    section: str
    academic_year: str
    class_code: str
    is_active: bool
    allow_rep_poll_creation: bool
    created_at: datetime
    total_students: int = 0
    total_teachers: int = 0
    total_reps: int = 0
    active_polls: int = 0
    is_rep: bool = False
    is_teacher: bool = False
    assigned_teachers: List[ClassTeacherDetail] = []

class ClassJoinRequest(BaseModel):
    class_code: str = Field(..., min_length=4, max_length=20)

class ClassMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    email: str
    register_number: Optional[str] = None
    department: Optional[str] = None
    year: Optional[int] = None
    section: Optional[str] = None
    phone_number: Optional[str] = None
    joined_at: datetime
    is_rep: bool = False
    is_active: bool = True
    is_muted: bool = False

class AssignRepRequest(BaseModel):
    student_id: int

class AssignTeacherRequest(BaseModel):
    teacher_id: int

class AddStudentToClassRequest(BaseModel):
    student_id: Optional[int] = None
    register_number: Optional[str] = None

class MuteStudentRequest(BaseModel):
    is_muted: bool
