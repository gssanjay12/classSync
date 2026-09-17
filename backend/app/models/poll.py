from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
from app.models.enums import PollStatus

def utc_now():
    return datetime.now(timezone.utc)

class Poll(Base):
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(20), unique=True, index=True, nullable=False) # e.g. "8F72KQX9"
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(String(500), nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(SQLEnum(PollStatus, native_enum=False), default=PollStatus.ACTIVE, nullable=False, index=True)
    allow_response_editing = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    class_ = relationship("Class", back_populates="polls")
    creator = relationship("User", back_populates="created_polls")
    options = relationship("PollOption", back_populates="poll", cascade="all, delete-orphan", order_by="PollOption.position")
    responses = relationship("Response", back_populates="poll", cascade="all, delete-orphan")

class PollOption(Base):
    __tablename__ = "poll_options"

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=False, index=True)
    option_text = Column(String(255), nullable=False)
    position = Column(Integer, default=0, nullable=False)

    poll = relationship("Poll", back_populates="options")
    responses = relationship("Response", back_populates="option", cascade="all, delete-orphan")

class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    option_id = Column(Integer, ForeignKey("poll_options.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    poll = relationship("Poll", back_populates="responses")
    student = relationship("User", back_populates="responses")
    option = relationship("PollOption", back_populates="responses")

    __table_args__ = (
        UniqueConstraint("poll_id", "student_id", name="uq_poll_student_response"),
    )
