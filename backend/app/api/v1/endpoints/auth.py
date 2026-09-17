from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.config import settings
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_token,
    generate_random_token
)
from app.core.rate_limit import rate_limit_auth
from app.core.audit import record_audit_log
from app.models.user import User, StudentProfile, TeacherProfile
from app.models.token import RefreshToken, EmailVerificationToken, PasswordResetToken
from app.models.enums import UserRole, UserStatus
from app.schemas.auth import (
    StudentRegisterRequest,
    TeacherRegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    MessageResponse
)
from app.schemas.user import UserResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit_auth)])
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    identifier = req.email.strip()
    identifier_lower = identifier.lower()

    # 1. Match by exact email or exact name (case-insensitive)
    user = db.query(User).filter(
        or_(
            func.lower(User.email) == identifier_lower,
            func.lower(User.name) == identifier_lower
        )
    ).first()

    # 2. If not found, match by student register number
    if not user:
        profile = db.query(StudentProfile).filter(
            func.lower(StudentProfile.register_number) == identifier_lower
        ).first()
        if profile:
            user = db.query(User).filter(User.id == profile.user_id).first()

    # 3. If not found, match prefix of name (e.g. "Rahul" -> "Rahul V", "Sanjay" -> "Sanjay G S")
    if not user:
        user = db.query(User).filter(
            func.lower(User.name).startswith(identifier_lower)
        ).first()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid name/email or password.")
    
    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account has been suspended.")
    if user.status == UserStatus.DEACTIVATED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account has been deactivated.")
    if user.status == UserStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is awaiting administrator approval.")

    user.last_login_at = datetime.now(timezone.utc)
    
    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh_token_str = create_refresh_token({"sub": str(user.id)})

    rt_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token_str),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(rt_record)
    db.commit()

    client_ip = request.client.host if request.client else None
    record_audit_log(db, action="LOGIN", target_type="USER", actor_user_id=user.id, target_id=str(user.id), ip_address=client_ip)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        user_id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        status=user.status
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_refresh_token(req.refresh_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token payload")

    token_h = hash_token(req.refresh_token)
    rt = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_h,
        RefreshToken.user_id == int(user_id),
        RefreshToken.revoked_at.is_(None)
    ).first()

    if not rt:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked or does not exist")

    # Rotate refresh token: revoke old one
    rt.revoked_at = datetime.now(timezone.utc)

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or user.status != UserStatus.ACTIVE:
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active")

    new_access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})

    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(new_rt)
    db.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user_id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        status=user.status
    )

@router.post("/logout", response_model=MessageResponse)
def logout(req: RefreshTokenRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    token_h = hash_token(req.refresh_token)
    rt = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_h,
        RefreshToken.user_id == current_user.id
    ).first()
    if rt:
        rt.revoked_at = datetime.now(timezone.utc)
        db.commit()
    return MessageResponse(message="Successfully logged out")

@router.post("/forgot-password", response_model=MessageResponse, dependencies=[Depends(rate_limit_auth)])
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if user:
        raw_token = generate_random_token(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        db.add(reset_token)
        db.commit()
        # In production, dispatch SMTP email with raw_token link
        # Generic response to prevent account enumeration
    return MessageResponse(message="If an account exists for this email, a password reset link has been sent.")

@router.post("/reset-password", response_model=MessageResponse, dependencies=[Depends(rate_limit_auth)])
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_h = hash_token(req.token)
    reset_entry = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_h,
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.expires_at > datetime.now(timezone.utc)
    ).first()

    if not reset_entry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == reset_entry.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password_hash = get_password_hash(req.new_password)
    reset_entry.used_at = datetime.now(timezone.utc)

    # Invalidate all current refresh tokens for this user upon password reset
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked_at.is_(None)
    ).update({"revoked_at": datetime.now(timezone.utc)})

    db.commit()
    return MessageResponse(message="Password has been successfully updated. You may now log in.")

@router.post("/verify-email", response_model=MessageResponse)
def verify_email(req: VerifyEmailRequest, db: Session = Depends(get_db)):
    token_h = hash_token(req.token)
    token_entry = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token_hash == token_h,
        EmailVerificationToken.used_at.is_(None),
        EmailVerificationToken.expires_at > datetime.now(timezone.utc)
    ).first()

    if not token_entry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")

    user = db.query(User).filter(User.id == token_entry.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.email_verified = True
    token_entry.used_at = datetime.now(timezone.utc)
    db.commit()

    return MessageResponse(message="Email verified successfully.")

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.class_model import ClassRepresentative, ClassTeacher, Class
    # Query user's REP and Teacher assigned classes
    rep_assignments = db.query(ClassRepresentative, Class).join(Class, ClassRepresentative.class_id == Class.id).filter(
        ClassRepresentative.student_id == current_user.id,
        ClassRepresentative.is_active == True,
        Class.is_active == True
    ).all()
    rep_classes = [{"class_id": c.id, "class_name": c.name} for _, c in rep_assignments]

    teacher_assignments = db.query(ClassTeacher, Class).join(Class, ClassTeacher.class_id == Class.id).filter(
        ClassTeacher.teacher_id == current_user.id,
        ClassTeacher.is_active == True,
        Class.is_active == True
    ).all()
    teacher_classes = [{"class_id": c.id, "class_name": c.name} for _, c in teacher_assignments]

    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        status=current_user.status,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at,
        student_profile=current_user.student_profile,
        teacher_profile=current_user.teacher_profile,
        rep_classes=rep_classes,
        teacher_classes=teacher_classes
    )
