from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.class_model import Class, ClassMember, ClassTeacher, ClassRepresentative
from app.models.poll import Poll
from app.models.enums import UserRole, UserStatus

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended. Please contact the administrator."
        )
    if user.status == UserStatus.DEACTIVATED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated."
        )

    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is awaiting approval or is inactive."
        )
    return current_user

class RoleChecker:
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to perform this action."
            )
        return user

require_faculty = RoleChecker([UserRole.FACULTY])
require_teacher_or_admin = require_faculty # Backward compatibility
require_student = RoleChecker([UserRole.STUDENT])

def check_teacher_or_rep_for_class(
    class_id: int,
    user: User,
    db: Session,
    for_poll_creation: bool = False
) -> Class:
    target_class = db.query(Class).filter(Class.id == class_id, Class.is_active == True).first()
    if not target_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or inactive"
        )

    # Check if user is an assigned faculty
    is_faculty = db.query(ClassTeacher).filter(
        ClassTeacher.class_id == class_id,
        ClassTeacher.teacher_id == user.id,
        ClassTeacher.is_active == True
    ).first()
    if is_faculty:
        return target_class

    # Check if user is an assigned REP
    is_rep = db.query(ClassRepresentative).filter(
        ClassRepresentative.class_id == class_id,
        ClassRepresentative.student_id == user.id,
        ClassRepresentative.is_active == True
    ).first()
    if is_rep:
        if for_poll_creation and not target_class.allow_rep_poll_creation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Poll creation by Representatives is disabled for this class."
            )
        return target_class

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to manage or view this class."
    )

def check_faculty_for_class(
    class_id: int,
    user: User,
    db: Session
) -> Class:
    target_class = db.query(Class).filter(Class.id == class_id, Class.is_active == True).first()
    if not target_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or inactive"
        )

    # Check if user is an assigned faculty
    is_faculty = db.query(ClassTeacher).filter(
        ClassTeacher.class_id == class_id,
        ClassTeacher.teacher_id == user.id,
        ClassTeacher.is_active == True
    ).first()
    if is_faculty:
        return target_class

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only faculty assigned to this class may perform this action."
    )

check_teacher_or_admin_for_class = check_faculty_for_class

def check_student_in_class(
    class_id: int,
    user: User,
    db: Session
) -> Class:
    target_class = db.query(Class).filter(Class.id == class_id, Class.is_active == True).first()
    if not target_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or inactive"
        )

    is_member = db.query(ClassMember).filter(
        ClassMember.class_id == class_id,
        ClassMember.student_id == user.id,
        ClassMember.is_active == True
    ).first()
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this class."
        )
    return target_class
