from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, StudentProfile
from app.schemas.user import UserResponse, UserProfileUpdate
from app.api.deps import get_current_active_user

router = APIRouter()

def build_user_response(user: User, db: Session) -> UserResponse:
    from app.models.class_model import ClassRepresentative, ClassTeacher, Class
    rep_assignments = db.query(ClassRepresentative, Class).join(Class, ClassRepresentative.class_id == Class.id).filter(
        ClassRepresentative.student_id == user.id,
        ClassRepresentative.is_active == True,
        Class.is_active == True
    ).all()
    rep_classes = [{"class_id": c.id, "class_name": c.name} for _, c in rep_assignments]

    teacher_assignments = db.query(ClassTeacher, Class).join(Class, ClassTeacher.class_id == Class.id).filter(
        ClassTeacher.teacher_id == user.id,
        ClassTeacher.is_active == True,
        Class.is_active == True
    ).all()
    teacher_classes = [{"class_id": c.id, "class_name": c.name} for _, c in teacher_assignments]

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        status=user.status,
        email_verified=user.email_verified,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        student_profile=user.student_profile,
        teacher_profile=user.teacher_profile,
        rep_classes=rep_classes,
        teacher_classes=teacher_classes
    )

@router.get("/me", response_model=UserResponse)
def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return build_user_response(current_user, db)

@router.patch("/me", response_model=UserResponse)
def update_user_profile(
    req: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if req.name is not None and req.name.strip():
        current_user.name = req.name.strip()
    
    if current_user.student_profile:
        if req.department is not None:
            current_user.student_profile.department = req.department.strip()
        if req.year is not None:
            current_user.student_profile.year = req.year
        if req.section is not None:
            current_user.student_profile.section = req.section.strip().upper()
    
    db.commit()
    db.refresh(current_user)
    return build_user_response(current_user, db)
