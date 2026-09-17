from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
from app.models.enums import UserRole, UserStatus

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole, native_enum=False), default=UserRole.STUDENT, nullable=False, index=True)
    status = Column(SQLEnum(UserStatus, native_enum=False), default=UserStatus.ACTIVE, nullable=False, index=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    class_memberships = relationship("ClassMember", back_populates="student", cascade="all, delete-orphan")
    teacher_assignments = relationship("ClassTeacher", foreign_keys="ClassTeacher.teacher_id", back_populates="teacher", cascade="all, delete-orphan")
    rep_assignments = relationship("ClassRepresentative", foreign_keys="ClassRepresentative.student_id", back_populates="student", cascade="all, delete-orphan")
    created_polls = relationship("Poll", back_populates="creator", cascade="all, delete-orphan")
    responses = relationship("Response", back_populates="student", cascade="all, delete-orphan")

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    register_number = Column(String(50), unique=True, index=True, nullable=False)
    department = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    section = Column(String(20), nullable=False)
    phone_number = Column(String(20), nullable=True) # WhatsApp number
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="student_profile")

class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    department = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=True) # WhatsApp number
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="teacher_profile")
