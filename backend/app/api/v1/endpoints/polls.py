from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from urllib.parse import quote
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.config import settings
from app.core.security import generate_poll_public_id
from app.core.audit import record_audit_log
from app.models.poll import Poll, PollOption, Response
from app.models.class_model import Class, ClassMember, ClassTeacher, ClassRepresentative
from app.models.user import User, StudentProfile
from app.models.message_log import MessageLog
from app.models.enums import UserRole, PollStatus
from app.services.whatsapp import WhatsAppService
from app.schemas.poll import (
    PollCreate,
    PollUpdate,
    PollResponse,
    PollOptionResponse
)
from app.schemas.response import (
    SubmitResponseRequest,
    ParticipantDetail,
    PollParticipantsResponse,
    PollRemindRequest,
    PollRemindResponse,
    MessageLogDetail
)
from app.schemas.auth import MessageResponse
from app.api.deps import (
    get_current_active_user,
    check_teacher_or_rep_for_class,
    check_student_in_class
)

router = APIRouter()

def build_poll_response(poll: Poll, user: User, db: Session) -> PollResponse:
    now = datetime.now(timezone.utc)
    # Check if deadline passed and auto-close status if active
    deadline = poll.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    is_closed = poll.status == PollStatus.CLOSED or poll.status == PollStatus.ARCHIVED or now > deadline

    # Total enrolled students in the class
    total_students = db.query(func.count(ClassMember.id)).filter(
        ClassMember.class_id == poll.class_id,
        ClassMember.is_active == True
    ).scalar() or 0

    # Total responses
    total_responses = db.query(func.count(Response.id)).filter(
        Response.poll_id == poll.id
    ).scalar() or 0

    completion_rate = round((total_responses / total_students * 100), 1) if total_students > 0 else 0.0

    # Response for current user
    user_response = db.query(Response).filter(
        Response.poll_id == poll.id,
        Response.student_id == user.id
    ).first()

    has_responded = user_response is not None
    selected_option_id = user_response.option_id if user_response else None

    # Options with vote counts
    option_counts = dict(
        db.query(Response.option_id, func.count(Response.id)).filter(
            Response.poll_id == poll.id
        ).group_by(Response.option_id).all()
    )

    options_data = []
    for opt in poll.options:
        votes = option_counts.get(opt.id, 0)
        pct = round((votes / total_responses * 100), 1) if total_responses > 0 else 0.0
        options_data.append(PollOptionResponse(
            id=opt.id,
            option_text=opt.option_text,
            position=opt.position,
            votes_count=votes,
            percentage=pct
        ))

    frontend_base = settings.FRONTEND_URL.rstrip('/')
    share_url = f"{frontend_base}/poll/{poll.public_id}"
    
    # Formatted WhatsApp share text
    whatsapp_text = f"*{poll.class_.name} Poll*\n\n{poll.question}\n\n👉 Submit your response here:\n{share_url}"
    whatsapp_share_url = f"https://api.whatsapp.com/send?text={quote(whatsapp_text)}"

    return PollResponse(
        id=poll.id,
        public_id=poll.public_id,
        class_id=poll.class_id,
        class_name=poll.class_.name,
        creator_id=poll.creator_id,
        creator_name=poll.creator.name,
        question=poll.question,
        deadline=poll.deadline,
        status=poll.status,
        allow_response_editing=poll.allow_response_editing,
        created_at=poll.created_at,
        options=options_data,
        has_responded=has_responded,
        selected_option_id=selected_option_id,
        total_students=total_students,
        total_responses=total_responses,
        completion_rate=completion_rate,
        is_closed=is_closed,
        share_url=share_url,
        whatsapp_share_url=whatsapp_share_url
    )

@router.post("/classes/{class_id}/polls", response_model=PollResponse)
def create_poll(
    class_id: int,
    req: PollCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    cls = check_teacher_or_rep_for_class(class_id, current_user, db, for_poll_creation=True)

    # Deadline validation
    now = datetime.now(timezone.utc)
    deadline = req.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    if deadline <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Poll deadline must be in the future.")

    # Generate unique public_id
    public_id = generate_poll_public_id()
    while db.query(Poll).filter(Poll.public_id == public_id).first():
        public_id = generate_poll_public_id()

    poll = Poll(
        public_id=public_id,
        class_id=cls.id,
        creator_id=current_user.id,
        question=req.question.strip(),
        deadline=deadline,
        status=PollStatus.ACTIVE,
        allow_response_editing=req.allow_response_editing
    )
    db.add(poll)
    db.flush()

    for idx, opt_text in enumerate(req.options):
        if opt_text.strip():
            opt = PollOption(
                poll_id=poll.id,
                option_text=opt_text.strip(),
                position=idx
            )
            db.add(opt)

    db.commit()
    db.refresh(poll)

    client_ip = request.client.host if request.client else None
    record_audit_log(db, action="CREATE_POLL", target_type="POLL", actor_user_id=current_user.id, target_id=str(poll.id), metadata={"question": poll.question, "class_id": class_id}, ip_address=client_ip)

    return build_poll_response(poll, current_user, db)

@router.get("/classes/{class_id}/polls", response_model=List[PollResponse])
def get_class_polls(
    class_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    cls = db.query(Class).filter(Class.id == class_id, Class.is_active == True).first()
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    # Authorize: must be assigned faculty or enrolled student/rep
    is_member = db.query(ClassMember).filter(ClassMember.class_id == class_id, ClassMember.student_id == current_user.id, ClassMember.is_active == True).first()
    is_teacher = db.query(ClassTeacher).filter(ClassTeacher.class_id == class_id, ClassTeacher.teacher_id == current_user.id, ClassTeacher.is_active == True).first()
    if not is_member and not is_teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view polls for this class.")

    polls = db.query(Poll).filter(Poll.class_id == class_id).order_by(Poll.created_at.desc()).all()
    return [build_poll_response(p, current_user, db) for p in polls]

@router.get("/public/{public_id}", response_model=PollResponse)
def get_public_poll(
    public_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    poll = db.query(Poll).filter(Poll.public_id == public_id.strip()).first()
    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poll does not exist or has been removed.")

    # Verify student or teacher belongs to poll's class
    is_member = db.query(ClassMember).filter(ClassMember.class_id == poll.class_id, ClassMember.student_id == current_user.id, ClassMember.is_active == True).first()
    is_teacher = db.query(ClassTeacher).filter(ClassTeacher.class_id == poll.class_id, ClassTeacher.teacher_id == current_user.id, ClassTeacher.is_active == True).first()
    if not is_member and not is_teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are not enrolled in {poll.class_.name}. You must be a member of this class to participate in this poll."
        )

    return build_poll_response(poll, current_user, db)

@router.get("/{id}", response_model=PollResponse)
def get_poll_by_id(
    id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    poll = db.query(Poll).filter(Poll.id == id).first()
    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poll not found")
    
    is_member = db.query(ClassMember).filter(ClassMember.class_id == poll.class_id, ClassMember.student_id == current_user.id, ClassMember.is_active == True).first()
    is_teacher = db.query(ClassTeacher).filter(ClassTeacher.class_id == poll.class_id, ClassTeacher.teacher_id == current_user.id, ClassTeacher.is_active == True).first()
    if not is_member and not is_teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this poll.")

    return build_poll_response(poll, current_user, db)

@router.patch("/{id}", response_model=PollResponse)
def update_poll(
    id: int,
    req: PollUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    poll = db.query(Poll).filter(Poll.id == id).first()
    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poll not found")

    # Only creator or assigned faculty can update
    check_teacher_or_rep_for_class(poll.class_id, current_user, db)

    is_assigned_teacher = db.query(ClassTeacher).filter(
        ClassTeacher.class_id == poll.class_id,
        ClassTeacher.teacher_id == current_user.id,
        ClassTeacher.is_active == True
    ).first() is not None

    if not is_assigned_teacher and poll.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify polls that you created, or you must be an assigned faculty member."
        )

    if req.question is not None and req.question.strip():
        poll.question = req.question.strip()
    if req.deadline is not None:
        deadline = req.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        poll.deadline = deadline
    if req.status is not None:
        poll.status = req.status
    if req.allow_response_editing is not None:
        poll.allow_response_editing = req.allow_response_editing

    db.commit()
    db.refresh(poll)

    client_ip = request.client.host if request.client else None
    record_audit_log(db, action="UPDATE_POLL", target_type="POLL", actor_user_id=current_user.id, target_id=str(poll.id), ip_address=client_ip)

    return build_poll_response(poll, current_user, db)

@router.delete("/{id}", response_model=MessageResponse)
def delete_poll(
    id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    poll = db.query(Poll).filter(Poll.id == id).first()
    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poll not found")

    check_teacher_or_rep_for_class(poll.class_id, current_user, db)

    is_assigned_teacher = db.query(ClassTeacher).filter(
        ClassTeacher.class_id == poll.class_id,
        ClassTeacher.teacher_id == current_user.id,
        ClassTeacher.is_active == True
    ).first() is not None

    if not is_assigned_teacher and poll.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete polls that you created, or you must be an assigned faculty member."
        )

    db.delete(poll)
    db.commit()

    client_ip = request.client.host if request.client else None
    record_audit_log(db, action="DELETE_POLL", target_type="POLL", actor_user_id=current_user.id, target_id=str(id), ip_address=client_ip)

    return MessageResponse(message="Poll deleted successfully.")

@router.post("/{id}/respond", response_model=PollResponse)
def submit_response(
    id: int,
    req: SubmitResponseRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    poll = db.query(Poll).filter(Poll.id == id).first()
    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poll not found")

    # Check student is enrolled in poll's class and not muted
    member = db.query(ClassMember).filter(
        ClassMember.class_id == poll.class_id,
        ClassMember.student_id == current_user.id,
        ClassMember.is_active == True
    ).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not enrolled in this class.")
    if member.is_muted:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are currently muted in this class and cannot submit responses.")

    # Check deadline
    now = datetime.now(timezone.utc)
    deadline = poll.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    
    if poll.status != PollStatus.ACTIVE or now > deadline:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This poll is closed and no longer accepting responses.")

    # Validate option belongs to this poll
    option = db.query(PollOption).filter(
        PollOption.id == req.option_id,
        PollOption.poll_id == poll.id
    ).first()
    if not option:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid option selected.")

    existing_response = db.query(Response).filter(
        Response.poll_id == poll.id,
        Response.student_id == current_user.id
    ).first()

    if existing_response:
        if not poll.allow_response_editing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already submitted this poll.")
        existing_response.option_id = req.option_id
        existing_response.updated_at = datetime.now(timezone.utc)
    else:
        new_response = Response(
            poll_id=poll.id,
            student_id=current_user.id,
            option_id=req.option_id,
            submitted_at=datetime.now(timezone.utc)
        )
        db.add(new_response)

    db.commit()
    db.refresh(poll)

    client_ip = request.client.host if request.client else None
    record_audit_log(db, action="SUBMIT_RESPONSE", target_type="POLL", actor_user_id=current_user.id, target_id=str(poll.id), ip_address=client_ip)

    return build_poll_response(poll, current_user, db)

@router.get("/{id}/participants", response_model=PollParticipantsResponse)
def get_poll_participants(
    id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    poll = db.query(Poll).filter(Poll.id == id).first()
    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poll not found")

    # Authorize: Only Teacher of class, REP of class, or Admin can view DONE / NOT DONE participants
    check_teacher_or_rep_for_class(poll.class_id, current_user, db)

    now = datetime.now(timezone.utc)
    deadline = poll.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    is_closed = poll.status == PollStatus.CLOSED or poll.status == PollStatus.ARCHIVED or now > deadline

    # All active enrolled students in this class
    class_students = db.query(User, StudentProfile).join(
        ClassMember, ClassMember.student_id == User.id
    ).outerjoin(
        StudentProfile, StudentProfile.user_id == User.id
    ).filter(
        ClassMember.class_id == poll.class_id,
        ClassMember.is_active == True
    ).order_by(StudentProfile.register_number.asc(), User.name.asc()).all()

    # All responses for this poll
    responses = db.query(Response, PollOption).join(
        PollOption, Response.option_id == PollOption.id
    ).filter(
        Response.poll_id == poll.id
    ).all()

    # Map student_id -> (Response, PollOption)
    resp_map = {r.student_id: (r, opt) for r, opt in responses}

    done_students: List[ParticipantDetail] = []
    not_done_students: List[ParticipantDetail] = []

    for user, profile in class_students:
        reg_num = profile.register_number if profile else None
        phone = profile.phone_number if profile else None
        if user.id in resp_map:
            resp, opt = resp_map[user.id]
            done_students.append(ParticipantDetail(
                student_id=user.id,
                name=user.name,
                register_number=reg_num,
                email=user.email,
                phone_number=phone,
                option_id=opt.id,
                option_text=opt.option_text,
                submitted_at=resp.submitted_at
            ))
        else:
            not_done_students.append(ParticipantDetail(
                student_id=user.id,
                name=user.name,
                register_number=reg_num,
                email=user.email,
                phone_number=phone,
                option_id=None,
                option_text=None,
                submitted_at=None
            ))

    total_students = len(class_students)
    completed_count = len(done_students)
    pending_count = len(not_done_students)
    completion_rate = round((completed_count / total_students * 100), 1) if total_students > 0 else 0.0

    # Option counts
    option_counts = dict(
        db.query(Response.option_id, func.count(Response.id)).filter(
            Response.poll_id == poll.id
        ).group_by(Response.option_id).all()
    )

    options_data = []
    for opt in poll.options:
        votes = option_counts.get(opt.id, 0)
        pct = round((votes / completed_count * 100), 1) if completed_count > 0 else 0.0
        options_data.append(PollOptionResponse(
            id=opt.id,
            option_text=opt.option_text,
            position=opt.position,
            votes_count=votes,
            percentage=pct
        ))

    return PollParticipantsResponse(
        poll_id=poll.id,
        public_id=poll.public_id,
        creator_id=poll.creator_id,
        question=poll.question,
        class_id=poll.class_id,
        class_name=poll.class_.name,
        deadline=poll.deadline,
        is_closed=is_closed,
        total_students=total_students,
        completed_count=completed_count,
        pending_count=pending_count,
        completion_rate=completion_rate,
        done_students=done_students,
        not_done_students=not_done_students,
        options=options_data
    )

@router.post("/{id}/remind", response_model=PollRemindResponse)
def send_poll_reminders(
    id: int,
    req: PollRemindRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    poll = db.query(Poll).filter(Poll.id == id).first()
    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poll not found")

    # Authorize: caller must be assigned Faculty or REP for this class
    check_teacher_or_rep_for_class(poll.class_id, current_user, db)

    now = datetime.now(timezone.utc)
    deadline = poll.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    if poll.status != PollStatus.ACTIVE or now > deadline:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot send reminders for closed or expired polls.")

    # Get all enrolled students who haven't responded
    responded_ids = [r.student_id for r in db.query(Response.student_id).filter(Response.poll_id == poll.id).all()]

    target_query = db.query(User, StudentProfile).join(
        ClassMember, ClassMember.student_id == User.id
    ).outerjoin(
        StudentProfile, StudentProfile.user_id == User.id
    ).filter(
        ClassMember.class_id == poll.class_id,
        ClassMember.is_active == True,
        ClassMember.is_muted == False
    )

    if responded_ids:
        target_query = target_query.filter(~User.id.in_(responded_ids))

    if req.student_ids:
        target_query = target_query.filter(User.id.in_(req.student_ids))

    targets = target_query.all()
    if not targets:
        return PollRemindResponse(
            total_targeted=0,
            sent_count=0,
            failed_count=0,
            results=[]
        )

    poll_link = f"{settings.FRONTEND_URL}/poll/{poll.public_id}"
    deadline_str = deadline.strftime("%d %b %Y, %I:%M %p UTC")

    results = []
    sent_count = 0
    failed_count = 0

    for user, profile in targets:
        raw_phone = profile.phone_number if profile else None
        send_res = WhatsAppService.send_poll_reminder(
            db=db,
            student_id=user.id,
            poll_id=poll.id,
            sent_by_id=current_user.id,
            student_name=user.name,
            recipient_phone=raw_phone or "",
            poll_question=poll.question,
            deadline_str=deadline_str,
            poll_link=poll_link,
            custom_message=req.custom_message
        )
        if send_res["success"]:
            sent_count += 1
        else:
            failed_count += 1

        results.append(MessageLogDetail(
            id=0,
            poll_id=poll.id,
            student_id=user.id,
            student_name=user.name,
            recipient_phone=raw_phone or "N/A",
            message_type="POLL_REMINDER",
            provider="WHATSAPP_CLOUD_API",
            provider_message_id=send_res.get("message_id"),
            delivery_status=send_res.get("status", "SENT"),
            error_message=send_res.get("error"),
            sent_at=now
        ))

    client_ip = request.client.host if request.client else None
    record_audit_log(db, action="SEND_WHATSAPP_REMINDERS", target_type="POLL", actor_user_id=current_user.id, target_id=str(poll.id), metadata={"targeted": len(targets), "sent": sent_count, "failed": failed_count}, ip_address=client_ip)

    return PollRemindResponse(
        total_targeted=len(targets),
        sent_count=sent_count,
        failed_count=failed_count,
        results=results
    )

@router.get("/{id}/messages", response_model=List[MessageLogDetail])
def get_poll_messages(
    id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    poll = db.query(Poll).filter(Poll.id == id).first()
    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poll not found")

    check_teacher_or_rep_for_class(poll.class_id, current_user, db)

    logs = db.query(MessageLog, User).join(
        User, MessageLog.student_id == User.id
    ).filter(
        MessageLog.poll_id == id
    ).order_by(MessageLog.sent_at.desc()).all()

    return [
        MessageLogDetail(
            id=log.id,
            poll_id=log.poll_id,
            student_id=log.student_id,
            student_name=user.name,
            recipient_phone=log.recipient_phone,
            message_type=log.message_type,
            provider=log.provider,
            provider_message_id=log.provider_message_id,
            delivery_status=log.delivery_status,
            error_message=log.error_message,
            sent_at=log.sent_at
        ) for log, user in logs
    ]
