from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.database import get_db
from app.models.user import User, StudentProfile
from app.models.enums import UserRole, UserStatus
from app.api.deps import require_faculty

router = APIRouter()

class StudentSearchItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    register_number: Optional[str] = None
    department: Optional[str] = None
    year: Optional[int] = None
    section: Optional[str] = None
    phone_number: Optional[str] = None

@router.get("/search", response_model=List[StudentSearchItem])
def search_students(
    q: str = Query(..., min_length=1, description="Search query matching name, email, or register number"),
    limit: int = Query(25, ge=1, le=100),
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    """
    Search database students by register number, name, or email to add them to classes.
    Restricted to Faculty.
    """
    search_term = f"%{q.strip()}%"

    query = db.query(User, StudentProfile).outerjoin(
        StudentProfile, User.id == StudentProfile.user_id
    ).filter(
        User.role == UserRole.STUDENT,
        User.status == UserStatus.ACTIVE,
        or_(
            User.name.ilike(search_term),
            User.email.ilike(search_term),
            StudentProfile.register_number.ilike(search_term),
            StudentProfile.department.ilike(search_term)
        )
    ).limit(limit)

    results = []
    for user, profile in query.all():
        results.append(StudentSearchItem(
            id=user.id,
            name=user.name,
            email=user.email,
            register_number=profile.register_number if profile else None,
            department=profile.department if profile else None,
            year=profile.year if profile else None,
            section=profile.section if profile else None,
            phone_number=profile.phone_number if profile else None
        ))

    return results
