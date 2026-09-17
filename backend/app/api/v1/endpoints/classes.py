from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.core.security import generate_class_code
from app.core.audit import record_audit_log
from app.models.class_model import Class, ClassMember, ClassTeacher, ClassRepresentative
from app.models.user import User, StudentProfile, TeacherProfile
from app.models.poll import Poll
from app.models.enums import UserRole, PollStatus
from app.schemas.class_schema import (
    ClassCreate,
    ClassUpdate,
    ClassResponse,
    ClassTeacherDetail,
    ClassJoinRequest,
    ClassMemberResponse,
    AssignRepRequest,
    AssignTeacherRequest,
    AddStudentToClassRequest,
    MuteStudentRequest
)
from app.schemas.auth import MessageResponse
from app.api.deps import (
    get_current_active_user,
    require_faculty,
    require_teacher_or_admin,
    check_teacher_or_rep_for_class,
    check_faculty_for_class,
    check_teacher_or_admin_for_class
)

router = APIRouter()

def build_class_response(cls: Class, user: User, db: Session) -> ClassResponse:
    student_count = db.query(func.count(ClassMember.id)).filter(
        ClassMember.class_id == cls.id,
        ClassMember.is_active == True
    ).scalar() or 0

    teacher_count = db.query(func.count(ClassTeacher.id)).filter(
        ClassTeacher.class_id == cls.id,
        ClassTeacher.is_active == True
    ).scalar() or 0

    rep_count = db.query(func.count(ClassRepresentative.id)).filter(
        ClassRepresentative.class_id == cls.id,
        ClassRepresentative.is_active == True
    ).scalar() or 0

    active_poll_count = db.query(func.count(Poll.id)).filter(
        Poll.class_id == cls.id,
        Poll.status == PollStatus.ACTIVE
    ).scalar() or 0

    is_rep = False
    is_teacher = False
    if user.role in (UserRole.FACULTY, UserRole.TEACHER):
        is_teacher = db.query(ClassTeacher).filter(
            ClassTeacher.class_id == cls.id,
            ClassTeacher.teacher_id == user.id,
            ClassTeacher.is_active == True
        ).first() is not None
    else:
        is_rep = db.query(ClassRepresentative).filter(
            ClassRepresentative.class_id == cls.id,
            ClassRepresentative.student_id == user.id,
            ClassRepresentative.is_active == True
        ).first() is not None

    teacher_assignments = db.query(ClassTeacher, User, TeacherProfile).join(
        User, ClassTeacher.teacher_id == User.id
    ).outerjoin(
        TeacherProfile, TeacherProfile.user_id == User.id
    ).filter(
        ClassTeacher.class_id == cls.id,
        ClassTeacher.is_active == True
    ).all()

    assigned_teachers_list = [
        ClassTeacherDetail(
            id=u.id,
            teacher_id=u.id,
            name=u.name,
            email=u.email,
            employee_id=tp.employee_id if tp else None
        ) for ct, u, tp in teacher_assignments
    ]

    return ClassResponse(
        id=cls.id,
        name=cls.name,
        department=cls.department,
        year=cls.year,
        section=cls.section,
        academic_year=cls.academic_year,
        class_code=cls.class_code,
        is_active=cls.is_active,
        allow_rep_poll_creation=cls.allow_rep_poll_creation,
        created_at=cls.created_at,
        total_students=student_count,
        total_teachers=teacher_count,
        total_reps=rep_count,
        active_polls=active_poll_count,
        is_rep=is_rep,
        is_teacher=is_teacher,
        assigned_teachers=assigned_teachers_list
    )

@router.get("", response_model=List[ClassResponse])
def list_classes(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role in (UserRole.FACULTY, UserRole.TEACHER):
        classes = db.query(Class).join(ClassTeacher, ClassTeacher.class_id == Class.id).filter(
            ClassTeacher.teacher_id == current_user.id,
            ClassTeacher.is_active == True,
            Class.is_active == True
        ).all()
    else:
        # Student or REP
        classes = db.query(Class).join(ClassMember, ClassMember.class_id == Class.id).filter(
            ClassMember.student_id == current_user.id,
            ClassMember.is_active == True,
            Class.is_active == True
        ).all()

    return [build_class_response(c, current_user, db) for c in classes]

@router.post("", response_model=ClassResponse)
def create_class(
    req: ClassCreate,
    request: Request,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    # Generate unique class code
    class_code = generate_class_code()
    while db.query(Class).filter(Class.class_code == class_code).first():
        class_code = generate_class_code()

    new_class = Class(
        name=req.name.strip(),
        department=req.department.strip(),
        year=req.year,
        section=req.section.strip().upper(),
        academic_year=req.academic_year.strip(),
        class_code=class_code,
        allow_rep_poll_creation=req.allow_rep_poll_creation
    )
    db.add(new_class)
    db.flush()

    # Automatically assign the creator faculty to the class
    assignment = ClassTeacher(
        class_id=new_class.id,
        teacher_id=current_user.id,
        assigned_by=current_user.id,
        is_active=True
    )
    db.add(assignment)
    db.commit()
    db.refresh(new_class)

    client_ip = request.client.host if request.client else None
    record_audit_log(db, action="CREATE_CLASS", target_type="CLASS", actor_user_id=current_user.id, target_id=str(new_class.id), metadata={"name": new_class.name, "code": new_class.class_code}, ip_address=client_ip)

    return build_class_response(new_class, current_user, db)

@router.get("/{id}", response_model=ClassResponse)
def get_class(
    id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    cls = db.query(Class).filter(Class.id == id, Class.is_active == True).first()
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    
    is_member = db.query(ClassMember).filter(ClassMember.class_id == id, ClassMember.student_id == current_user.id, ClassMember.is_active == True).first()
    is_teacher = db.query(ClassTeacher).filter(ClassTeacher.class_id == id, ClassTeacher.teacher_id == current_user.id, ClassTeacher.is_active == True).first()
    if not is_member and not is_teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to view this class.")

    return build_class_response(cls, current_user, db)

@router.patch("/{id}", response_model=ClassResponse)
def update_class(
    id: int,
    req: ClassUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    cls = check_faculty_for_class(id, current_user, db)
    
    if req.name is not None and req.name.strip():
        cls.name = req.name.strip()
    if req.department is not None:
        cls.department = req.department.strip()
    if req.year is not None:
        cls.year = req.year
    if req.section is not None:
        cls.section = req.section.strip().upper()
    if req.academic_year is not None:
        cls.academic_year = req.academic_year.strip()
    if req.allow_rep_poll_creation is not None:
        cls.allow_rep_poll_creation = req.allow_rep_poll_creation
    if req.is_active is not None:
        cls.is_active = req.is_active

    db.commit()
    db.refresh(cls)

    client_ip = request.client.host if request.client else None
    record_audit_log(db, action="UPDATE_CLASS", target_type="CLASS", actor_user_id=current_user.id, target_id=str(cls.id), ip_address=client_ip)

    return build_class_response(cls, current_user, db)

@router.post("/join", response_model=ClassResponse)
def join_class(
    req: ClassJoinRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    cls = db.query(Class).filter(Class.class_code == req.class_code.strip().upper(), Class.is_active == True).first()
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid class code or class is inactive.")

    existing_member = db.query(ClassMember).filter(
        ClassMember.class_id == cls.id,
        ClassMember.student_id == current_user.id
    ).first()

    if existing_member:
        if not existing_member.is_active:
            existing_member.is_active = True
            db.commit()
            return build_class_response(cls, current_user, db)
        else:
            return build_class_response(cls, current_user, db)

    member = ClassMember(
        class_id=cls.id,
        student_id=current_user.id,
        is_active=True
    )
    db.add(member)
    db.commit()

    client_ip = request.client.host if request.client else None
    record_audit_log(db, action="JOIN_CLASS", target_type="CLASS", actor_user_id=current_user.id, target_id=str(cls.id), ip_address=client_ip)

    return build_class_response(cls, current_user, db)

@router.get("/{id}/students", response_model=List[ClassMemberResponse])
def get_class_students(
    id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    cls = check_teacher_or_rep_for_class(id, current_user, db)
    
    # Query all active students in this class with their profile
    members = db.query(ClassMember, User, StudentProfile).join(
        User, ClassMember.student_id == User.id
    ).outerjoin(
        StudentProfile, StudentProfile.user_id == User.id
    ).filter(
        ClassMember.class_id == id,
        ClassMember.is_active == True
    ).order_by(StudentProfile.register_number.asc()).all()

    # Query reps in this class
    reps = {r.student_id for r in db.query(ClassRepresentative).filter(
        ClassRepresentative.class_id == id,
        ClassRepresentative.is_active == True
    ).all()}

    results = []
    for member, user, profile in members:
        results.append(ClassMemberResponse(
            id=member.id,
            user_id=user.id,
            name=user.name,
            email=user.email,
            register_number=profile.register_number if profile else None,
            department=profile.department if profile else None,
            year=profile.year if profile else None,
            section=profile.section if profile else None,
            phone_number=profile.phone_number if profile else None,
            joined_at=member.joined_at,
            is_rep=(user.id in reps),
            is_active=member.is_active,
            is_muted=member.is_muted
        ))

    return results

@router.post("/{id}/students", response_model=ClassMemberResponse)
def add_student_to_class(
    id: int,
    req: AddStudentToClassRequest,
    request: Request,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    cls = check_faculty_for_class(id, current_user, db)

    target_student = None
    if req.student_id:
        target_student = db.query(User).filter(User.id == req.student_id, User.role == UserRole.STUDENT).first()
    elif req.register_number:
        profile = db.query(StudentProfile).filter(StudentProfile.register_number == req.register_number.strip().upper()).first()
        if profile:
            target_student = db.query(User).filter(User.id == profile.user_id, User.role == UserRole.STUDENT).first()

    if not target_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found in institutional database.")

    member = db.query(ClassMember).filter(
        ClassMember.class_id == id,
        ClassMember.student_id == target_student.id
    ).first()

    if member:
        member.is_active = True
    else:
        member = ClassMember(
            class_id=id,
            student_id=target_student.id,
            is_active=True
        )
        db.add(member)

    db.commit()
    db.refresh(member)

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == target_student.id).first()
    reps = {r.student_id for r in db.query(ClassRepresentative).filter(
        ClassRepresentative.class_id == id,
        ClassRepresentative.is_active == True
    ).all()}

    client_ip = request.client.host if request.client else None
    record_audit_log(db, action="ADD_STUDENT_TO_CLASS", target_type="CLASS", actor_user_id=current_user.id, target_id=str(id), metadata={"student_id": target_student.id}, ip_address=client_ip)

    return ClassMemberResponse(
        id=member.id,
        user_id=target_student.id,
        name=target_student.name,
        email=target_student.email,
        register_number=profile.register_number if profile else None,
        department=profile.department if profile else None,
        year=profile.year if profile else None,
        section=profile.section if profile else None,
        phone_number=profile.phone_number if profile else None,
        joined_at=member.joined_at,
        is_rep=(target_student.id in reps),
        is_active=member.is_active,
        is_muted=member.is_muted
    )

@router.delete("/{id}/students/{student_id}", response_model=MessageResponse)
def remove_student_from_class(
    id: int,
    student_id: int,
    request: Request,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    cls = check_faculty_for_class(id, current_user, db)

    member = db.query(ClassMember).filter(
        ClassMember.class_id == id,
        ClassMember.student_id == student_id,
        ClassMember.is_active == True
    ).first()

    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student is not an active member of this class.")

    member.is_active = False

    # Deactivate REP if student was REP for this class
    rep_entry = db.query(ClassRepresentative).filter(
        ClassRepresentative.class_id == id,
        ClassRepresentative.student_id == student_id,
        ClassRepresentative.is_active == True
    ).first()
    if rep_entry:
        rep_entry.is_active = False

    db.commit()

    client_ip = request.client.host if request.client else None
    record_audit_log(db, action="REMOVE_STUDENT_FROM_CLASS", target_type="CLASS", actor_user_id=current_user.id, target_id=str(id), metadata={"student_id": student_id}, ip_address=client_ip)

    return MessageResponse(message="Student successfully removed from class.")

@router.patch("/{id}/members/{student_id}/mute", response_model=MessageResponse)
def mute_student_in_class(
    id: int,
    student_id: int,
    req: MuteStudentRequest,
    request: Request,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    cls = check_faculty_for_class(id, current_user, db)

    member = db.query(ClassMember).filter(
        ClassMember.class_id == id,
        ClassMember.student_id == student_id,
        ClassMember.is_active == True
    ).first()

    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student is not enrolled in this class.")

    member.is_muted = req.is_muted
    db.commit()

    action_name = "MUTE_STUDENT" if req.is_muted else "UNMUTE_STUDENT"
    client_ip = request.client.host if request.client else None
    record_audit_log(db, action=action_name, target_type="CLASS", actor_user_id=current_user.id, target_id=str(id), metadata={"student_id": student_id, "is_muted": req.is_muted}, ip_address=client_ip)

    status_msg = "muted" if req.is_muted else "unmuted"
    return MessageResponse(message=f"Student has been {status_msg} in this class.")

@router.post("/{id}/reps", response_model=MessageResponse)
def assign_rep(
    id: int,
    req: AssignRepRequest,
    request: Request,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    cls = check_faculty_for_class(id, current_user, db)

    # Student must be enrolled in class
    member = db.query(ClassMember).filter(
        ClassMember.class_id == id,
        ClassMember.student_id == req.student_id,
        ClassMember.is_active == True
    ).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student must be enrolled in the class before being assigned as REP.")

    # Check if already REP for this class
    rep_entry = db.query(ClassRepresentative).filter(
        ClassRepresentative.class_id == id,
        ClassRepresentative.student_id == req.student_id
    ).first()

    if rep_entry:
        rep_entry.is_active = True
    else:
        rep_entry = ClassRepresentative(
            class_id=id,
            student_id=req.student_id,
            assigned_by=current_user.id,
            is_active=True
        )
        db.add(rep_entry)

    db.commit()

    client_ip = request.client.host if request.client else None
    record_audit_log(db, action="ASSIGN_REP", target_type="CLASS", actor_user_id=current_user.id, target_id=str(id), metadata={"student_id": req.student_id}, ip_address=client_ip)

    return MessageResponse(message="Student successfully assigned as Class Representative.")

@router.delete("/{id}/reps/{student_id}", response_model=MessageResponse)
def remove_rep(
    id: int,
    student_id: int,
    request: Request,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    cls = check_faculty_for_class(id, current_user, db)

    rep_entry = db.query(ClassRepresentative).filter(
        ClassRepresentative.class_id == id,
        ClassRepresentative.student_id == student_id,
        ClassRepresentative.is_active == True
    ).first()

    if not rep_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student is not an active REP for this class.")

    rep_entry.is_active = False
    db.commit()

    client_ip = request.client.host if request.client else None
    record_audit_log(db, action="REMOVE_REP", target_type="CLASS", actor_user_id=current_user.id, target_id=str(id), metadata={"student_id": student_id}, ip_address=client_ip)

    return MessageResponse(message="Class Representative assignment removed.")

@router.post("/{id}/teachers", response_model=MessageResponse)
def assign_teacher(
    id: int,
    req: AssignTeacherRequest,
    request: Request,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    cls = db.query(Class).filter(Class.id == id, Class.is_active == True).first()
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    teacher = db.query(User).filter(User.id == req.teacher_id, User.role.in_([UserRole.FACULTY, UserRole.TEACHER])).first()
    if not teacher:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target user is not faculty.")

    assignment = db.query(ClassTeacher).filter(
        ClassTeacher.class_id == id,
        ClassTeacher.teacher_id == req.teacher_id
    ).first()

    if assignment:
        assignment.is_active = True
    else:
        assignment = ClassTeacher(
            class_id=id,
            teacher_id=req.teacher_id,
            assigned_by=current_user.id,
            is_active=True
        )
        db.add(assignment)

    db.commit()

    client_ip = request.client.host if request.client else None
    record_audit_log(db, action="ASSIGN_TEACHER", target_type="CLASS", actor_user_id=current_user.id, target_id=str(id), metadata={"teacher_id": req.teacher_id}, ip_address=client_ip)

    return MessageResponse(message="Faculty assigned to class successfully.")

@router.delete("/{id}/teachers/{teacher_id}", response_model=MessageResponse)
def remove_teacher(
    id: int,
    teacher_id: int,
    request: Request,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    assignment = db.query(ClassTeacher).filter(
        ClassTeacher.class_id == id,
        ClassTeacher.teacher_id == teacher_id,
        ClassTeacher.is_active == True
    ).first()

    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty is not assigned to this class.")

    assignment.is_active = False
    db.commit()

    client_ip = request.client.host if request.client else None
    record_audit_log(db, action="REMOVE_TEACHER", target_type="CLASS", actor_user_id=current_user.id, target_id=str(id), metadata={"teacher_id": teacher_id}, ip_address=client_ip)

    return MessageResponse(message="Faculty assignment removed.")
