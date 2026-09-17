from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False) # e.g. "AIDS-A"
    department = Column(String(100), nullable=False) # e.g. "AI & Data Science"
    year = Column(Integer, nullable=False) # e.g. 2
    section = Column(String(20), nullable=False) # e.g. "A"
    academic_year = Column(String(20), nullable=False, default="2026-27") # e.g. "2026-27"
    class_code = Column(String(20), unique=True, index=True, nullable=False) # e.g. "ADSA27"
    is_active = Column(Boolean, default=True, nullable=False)
    allow_rep_poll_creation = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    members = relationship("ClassMember", back_populates="class_", cascade="all, delete-orphan")
    teachers = relationship("ClassTeacher", back_populates="class_", cascade="all, delete-orphan")
    representatives = relationship("ClassRepresentative", back_populates="class_", cascade="all, delete-orphan")
    polls = relationship("Poll", back_populates="class_", cascade="all, delete-orphan")

class ClassMember(Base):
    __tablename__ = "class_members"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    joined_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_muted = Column(Boolean, default=False, nullable=False)

    class_ = relationship("Class", back_populates="members")
    student = relationship("User", back_populates="class_memberships")

    __table_args__ = (
        UniqueConstraint("class_id", "student_id", name="uq_class_student"),
    )

class ClassTeacher(Base):
    __tablename__ = "class_teachers"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    class_ = relationship("Class", back_populates="teachers")
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="teacher_assignments")

    __table_args__ = (
        UniqueConstraint("class_id", "teacher_id", name="uq_class_teacher"),
    )

class ClassRepresentative(Base):
    __tablename__ = "class_representatives"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    class_ = relationship("Class", back_populates="representatives")
    student = relationship("User", foreign_keys=[student_id], back_populates="rep_assignments")

    __table_args__ = (
        UniqueConstraint("class_id", "student_id", name="uq_class_rep"),
    )
