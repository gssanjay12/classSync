import re
import uuid
import logging
import httpx
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.config import settings
from app.models.message_log import MessageLog

logger = logging.getLogger("classpoll.whatsapp")

def clean_phone_number(raw_phone: str) -> Optional[str]:
    """Cleans phone number to standard E.164 digits format (e.g. 919876543210)."""
    if not raw_phone:
        return None
    # Strip any spaces, dashes, parens, plus
    digits = re.sub(r"[^\d]", "", raw_phone)
    if len(digits) == 10:
        # Default to India (+91) if 10-digit mobile
        digits = "91" + digits
    elif len(digits) < 10:
        return None
    return digits

class WhatsAppService:
    @staticmethod
    def send_poll_reminder(
        db: Session,
        student_id: int,
        poll_id: int,
        sent_by_id: int,
        student_name: str,
        recipient_phone: str,
        poll_question: str,
        deadline_str: str,
        poll_link: str,
        custom_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends an official WhatsApp reminder to a student regarding an active poll.
        Uses WhatsApp Cloud API (Graph API) when configured, or records simulated delivery in local/test dev.
        """
        cleaned_phone = clean_phone_number(recipient_phone)
        if not cleaned_phone:
            # Log failed attempt
            log_entry = MessageLog(
                poll_id=poll_id,
                student_id=student_id,
                sent_by=sent_by_id,
                recipient_phone=recipient_phone or "UNKNOWN",
                message_type="POLL_REMINDER",
                provider="WHATSAPP_CLOUD_API",
                delivery_status="FAILED",
                error_message="Invalid phone number format"
            )
            db.add(log_entry)
            db.commit()
            return {"success": False, "status": "FAILED", "error": "Invalid phone number format"}

        message_body = (
            custom_message or 
            f"Hello {student_name},\n\n"
            f"You have not yet responded to the ClassPoll:\n"
            f"\"{poll_question}\"\n\n"
            f"Please submit your response before: {deadline_str}\n\n"
            f"Participate here: {poll_link}"
        )

        has_credentials = bool(settings.WHATSAPP_PHONE_NUMBER_ID and settings.WHATSAPP_ACCESS_TOKEN)

        if has_credentials:
            url = f"{settings.WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
            headers = {
                "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": cleaned_phone,
                "type": "text",
                "text": {"preview_url": True, "body": message_body}
            }
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    if resp.status_code in (200, 201):
                        resp_data = resp.json()
                        wamid = resp_data.get("messages", [{}])[0].get("id", f"wamid.{uuid.uuid4().hex[:12]}")
                        delivery_status = "SENT"
                        error_msg = None
                    else:
                        wamid = None
                        delivery_status = "FAILED"
                        error_msg = f"HTTP {resp.status_code}: {resp.text}"
            except Exception as e:
                wamid = None
                delivery_status = "FAILED"
                error_msg = str(e)
        else:
            # Simulated delivery for dev / local testing
            wamid = f"wamid.simulated_{uuid.uuid4().hex[:16]}"
            delivery_status = "SENT"
            error_msg = None
            logger.info(
                f"[WhatsApp Cloud API Simulated Send] To: +{cleaned_phone} | Student: {student_name} | "
                f"Poll ID: {poll_id} | WAMID: {wamid}"
            )

        log_entry = MessageLog(
            poll_id=poll_id,
            student_id=student_id,
            sent_by=sent_by_id,
            recipient_phone=f"+{cleaned_phone}",
            message_type="POLL_REMINDER",
            provider="WHATSAPP_CLOUD_API",
            provider_message_id=wamid,
            delivery_status=delivery_status,
            error_message=error_msg
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        return {
            "success": delivery_status == "SENT",
            "status": delivery_status,
            "message_id": wamid,
            "error": error_msg,
            "sent_at": log_entry.sent_at.isoformat()
        }
