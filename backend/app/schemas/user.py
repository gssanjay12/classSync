from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.enums import UserRole, UserStatus

class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    register_number: str
    department: str
    year: int
    section: str

class TeacherProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: str
    department: str

class UserRepAssignment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    class_id: int
    class_name: str

class UserTeacherAssignment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    class_id: int
    class_name: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: UserRole
    status: UserStatus
    email_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    student_profile: Optional[StudentProfileResponse] = None
    teacher_profile: Optional[TeacherProfileResponse] = None
    rep_classes: Optional[List[UserRepAssignment]] = []
    teacher_classes: Optional[List[UserTeacherAssignment]] = []

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    year: Optional[int] = None
    section: Optional[str] = None
