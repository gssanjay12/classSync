from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import List
from app.database import get_db
from app.models.user import User, StudentProfile, TeacherProfile
from app.models.class_model import Class, ClassMember, ClassTeacher, ClassRepresentative
from app.models.poll import Poll, PollOption, Response
from app.models.enums import UserRole, UserStatus, PollStatus
from app.schemas.response import StudentDashboardStats, StudentHistoryItem, TeacherDashboardStats, FacultyDashboardStats
from app.schemas.poll import PollResponse
from app.api.deps import get_current_active_user, require_faculty
from app.api.v1.endpoints.polls import build_poll_response

router = APIRouter()

@router.get("/student", response_model=StudentDashboardStats)
def get_student_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    # Get all classes student is enrolled in
    class_ids = [m.class_id for m in db.query(ClassMember).filter(
        ClassMember.student_id == current_user.id,
        ClassMember.is_active == True
    ).all()]

    if not class_ids:
        return StudentDashboardStats(
            active_polls_count=0,
            completed_polls_count=0,
            pending_polls_count=0,
            completion_rate=0.0
        )

    # All polls in these classes
    all_polls = db.query(Poll).filter(Poll.class_id.in_(class_ids)).all()
    all_poll_ids = [p.id for p in all_polls]

    # Student responses
    responded_poll_ids = {r.poll_id for r in db.query(Response).filter(
        Response.student_id == current_user.id,
        Response.poll_id.in_(all_poll_ids)
    ).all()}

    # Active polls (status ACTIVE and deadline in future)
    active_polls_count = sum(1 for p in all_polls if p.status == PollStatus.ACTIVE and (p.deadline.tzinfo is not None and p.deadline > now or p.deadline.replace(tzinfo=timezone.utc) > now))
    completed_polls_count = len(responded_poll_ids)
    
    # Pending polls = active polls that student hasn't answered yet
    pending_polls_count = sum(1 for p in all_polls if p.id not in responded_poll_ids and p.status == PollStatus.ACTIVE and (p.deadline.tzinfo is not None and p.deadline > now or p.deadline.replace(tzinfo=timezone.utc) > now))

    total_polls_count = len(all_polls)
    completion_rate = round((completed_polls_count / total_polls_count * 100), 1) if total_polls_count > 0 else 0.0

    return StudentDashboardStats(
        active_polls_count=active_polls_count,
        completed_polls_count=completed_polls_count,
        pending_polls_count=pending_polls_count,
        completion_rate=completion_rate
    )

@router.get("/student/history", response_model=List[StudentHistoryItem])
def get_student_poll_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    # Get all classes student is enrolled in
    class_ids = [m.class_id for m in db.query(ClassMember).filter(
        ClassMember.student_id == current_user.id,
        ClassMember.is_active == True
    ).all()]

    if not class_ids:
        return []

    # All polls from student's classes
    polls = db.query(Poll).filter(Poll.class_id.in_(class_ids)).order_by(Poll.created_at.desc()).all()
    poll_ids = [p.id for p in polls]

    # All responses submitted by student
    user_responses = {
        r.poll_id: r for r in db.query(Response).filter(
            Response.student_id == current_user.id,
            Response.poll_id.in_(poll_ids)
        ).all()
    }

    # Fetch options for selected option text mapping
    options_map = {opt.id: opt.option_text for opt in db.query(PollOption).filter(PollOption.poll_id.in_(poll_ids)).all()}

    results = []
    for p in polls:
        resp = user_responses.get(p.id)
        deadline = p.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        is_closed = p.status == PollStatus.CLOSED or p.status == PollStatus.ARCHIVED or now > deadline

        results.append(StudentHistoryItem(
            poll_id=p.id,
            public_id=p.public_id,
            question=p.question,
            class_name=p.class_.name,
            deadline=p.deadline,
            is_closed=is_closed,
            is_done=(resp is not None),
            submitted_at=resp.submitted_at if resp else None,
            selected_option_text=options_map.get(resp.option_id) if resp else None
        ))

    return results

@router.get("/teacher", response_model=TeacherDashboardStats)
@router.get("/faculty", response_model=TeacherDashboardStats)
def get_faculty_dashboard(
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    classes = db.query(Class).join(ClassTeacher, ClassTeacher.class_id == Class.id).filter(
        ClassTeacher.teacher_id == current_user.id,
        ClassTeacher.is_active == True,
        Class.is_active == True
    ).all()

    class_ids = [c.id for c in classes]
    my_classes_count = len(classes)

    if not class_ids:
        return TeacherDashboardStats(
            my_classes_count=0,
            total_students=0,
            active_polls=0,
            average_completion_rate=0.0
        )

    # Total distinct students
    total_students = db.query(func.count(func.distinct(ClassMember.student_id))).filter(
        ClassMember.class_id.in_(class_ids),
        ClassMember.is_active == True
    ).scalar() or 0

    # Active polls
    polls = db.query(Poll).filter(Poll.class_id.in_(class_ids)).all()
    active_polls = sum(1 for p in polls if p.status == PollStatus.ACTIVE and (p.deadline.tzinfo is not None and p.deadline > now or p.deadline.replace(tzinfo=timezone.utc) > now))

    # Overall completion rate across faculty's polls
    rates = []
    for p in polls:
        total_p_students = db.query(func.count(ClassMember.id)).filter(
            ClassMember.class_id == p.class_id,
            ClassMember.is_active == True
        ).scalar() or 0
        p_responses = db.query(func.count(Response.id)).filter(Response.poll_id == p.id).scalar() or 0
        if total_p_students > 0:
            rates.append(p_responses / total_p_students * 100)

    avg_rate = round(sum(rates) / len(rates), 1) if rates else 0.0

    return TeacherDashboardStats(
        my_classes_count=my_classes_count,
        total_students=total_students,
        active_polls=active_polls,
        average_completion_rate=avg_rate
    )
