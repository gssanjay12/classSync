from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sent_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_phone = Column(String(30), nullable=False)
    message_type = Column(String(50), default="POLL_REMINDER", nullable=False)
    provider = Column(String(50), default="WHATSAPP_CLOUD_API", nullable=False)
    provider_message_id = Column(String(100), nullable=True, index=True)
    delivery_status = Column(String(50), default="SENT", nullable=False) # PENDING, SENT, DELIVERED, FAILED
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=True)

    poll = relationship("Poll")
    student = relationship("User", foreign_keys=[student_id])
    sender = relationship("User", foreign_keys=[sent_by])
