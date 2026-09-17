import re
import logging
import httpx
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.config import settings
from app.models.message_log import MessageLog

logger = logging.getLogger("classpoll.whatsapp")


def clean_phone_number(raw_phone: Optional[str]) -> Optional[str]:
    """
    Validates and normalizes phone number to official E.164 digits without leading '+'
    (e.g., '919876543210').
    Handles:
    - 10-digit Indian numbers: '9876543210' -> '919876543210'
    - 11-digit numbers with leading zero: '09876543210' -> '919876543210'
    - 12-digit Indian numbers: '919876543210' -> '919876543210'
    - International numbers: 10 to 15 digits
    Returns None if phone is empty, missing, or malformed.
    """
    if not raw_phone:
        return None

    # Strip whitespace, dashes, parentheses, dots, plus signs
    digits = re.sub(r"[^\d]", "", str(raw_phone).strip())

    if not digits:
        return None

    # Indian 10-digit mobile
    if len(digits) == 10:
        return f"91{digits}"

    # 11-digit starting with 0 (e.g. 09876543210)
    if len(digits) == 11 and digits.startswith("0"):
        return f"91{digits[1:]}"

    # 12-digit starting with 91 (e.g. 919876543210)
    if len(digits) == 12 and digits.startswith("91"):
        return digits

    # Other international numbers (E.164 allows 10-15 digits)
    if 10 <= len(digits) <= 15:
        return digits

    # Number is too short or too long
    return None


class WhatsAppService:
    @staticmethod
    def is_configured() -> bool:
        """Checks if real WhatsApp Cloud API integration is enabled and credentials are set."""
        return bool(
            settings.WHATSAPP_ENABLED
            and settings.WHATSAPP_PHONE_NUMBER_ID
            and settings.WHATSAPP_ACCESS_TOKEN
        )

    @classmethod
    def send_poll_reminder(
        cls,
        db: Session,
        student_id: int,
        poll_id: int,
        sent_by_id: int,
        student_name: str,
        recipient_phone: Optional[str],
        poll_question: str,
        deadline_str: str,
        poll_link: str,
        custom_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends an official WhatsApp reminder to a student regarding an active poll.
        Strictly uses Meta WhatsApp Cloud API when configured.
        When unconfigured or disabled, reports NOT_CONFIGURED without faking delivery.
        """
        cleaned_phone = clean_phone_number(recipient_phone)
        if not cleaned_phone:
            err = "WhatsApp number not available or invalid format"
            log_entry = MessageLog(
                poll_id=poll_id,
                student_id=student_id,
                sent_by=sent_by_id,
                recipient_phone=recipient_phone or "NOT_AVAILABLE",
                message_type="POLL_REMINDER",
                provider="WHATSAPP_CLOUD_API",
                provider_message_id=None,
                delivery_status="FAILED",
                error_message=err
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            return {
                "success": False,
                "status": "FAILED",
                "message_id": None,
                "log_id": log_entry.id,
                "error": err
            }

        # Check configuration
        if not cls.is_configured():
            err = "WhatsApp integration is not configured. Please set WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID."
            logger.warning(f"WhatsApp dispatch skipped for student {student_id}: {err}")
            log_entry = MessageLog(
                poll_id=poll_id,
                student_id=student_id,
                sent_by=sent_by_id,
                recipient_phone=f"+{cleaned_phone}",
                message_type="POLL_REMINDER",
                provider="WHATSAPP_CLOUD_API",
                provider_message_id=None,
                delivery_status="FAILED",
                error_message=err
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            return {
                "success": False,
                "status": "FAILED",
                "message_id": None,
                "log_id": log_entry.id,
                "error": err
            }

        # Official Meta WhatsApp Cloud API Endpoint
        base_api = settings.WHATSAPP_API_URL.rstrip("/")
        url = f"{base_api}/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        # Build message payload
        if settings.WHATSAPP_USE_TEMPLATE:
            # WhatsApp Cloud API pre-approved Template payload
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": cleaned_phone,
                "type": "template",
                "template": {
                    "name": settings.WHATSAPP_TEMPLATE_NAME,
                    "language": {
                        "code": settings.WHATSAPP_TEMPLATE_LANG
                    },
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": student_name},
                                {"type": "text", "text": poll_question[:120]},
                                {"type": "text", "text": deadline_str},
                                {"type": "text", "text": poll_link}
                            ]
                        }
                    ]
                }
            }
        else:
            # Freeform text fallback
            note = f"\n\nNote: {custom_message.strip()}" if custom_message and custom_message.strip() else ""
            message_body = (
                f"Hello {student_name},\n\n"
                f"You have not yet responded to the ClassPoll:\n"
                f"\"{poll_question}\"\n\n"
                f"Please submit your response before: {deadline_str}\n\n"
                f"Participate here: {poll_link}{note}"
            )
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": cleaned_phone,
                "type": "text",
                "text": {
                    "preview_url": True,
                    "body": message_body
                }
            }

        wamid = None
        delivery_status = "FAILED"
        error_msg = None

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code in (200, 201):
                    resp_data = resp.json()
                    messages = resp_data.get("messages", [])
                    if messages and "id" in messages[0]:
                        wamid = messages[0]["id"]
                        delivery_status = "SENT"
                        error_msg = None
                    else:
                        delivery_status = "FAILED"
                        error_msg = f"Unexpected provider response: {resp.text}"
                else:
                    delivery_status = "FAILED"
                    try:
                        err_json = resp.json().get("error", {})
                        meta_msg = err_json.get("message", resp.text)
                        meta_code = err_json.get("code", resp.status_code)
                        error_msg = f"WhatsApp API Error ({meta_code}): {meta_msg}"
                    except Exception:
                        error_msg = f"HTTP {resp.status_code}: {resp.text}"
        except httpx.TimeoutException:
            delivery_status = "FAILED"
            error_msg = "Request timed out connecting to WhatsApp API"
        except Exception as e:
            delivery_status = "FAILED"
            error_msg = f"Provider request error: {str(e)}"

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
            "log_id": log_entry.id,
            "error": error_msg,
            "sent_at": log_entry.sent_at.isoformat()
        }
