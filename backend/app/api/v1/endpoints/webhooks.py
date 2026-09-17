import logging
from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.database import get_db
from app.config import settings
from app.models.message_log import MessageLog

logger = logging.getLogger("classpoll.webhooks")

router = APIRouter()


@router.get("/whatsapp")
def verify_whatsapp_webhook(request: Request):
    """
    Webhook verification endpoint for Meta WhatsApp Cloud API.
    Handles the initial verification handshake.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        logger.info("[WhatsApp Webhook] Verification successful.")
        return Response(content=str(challenge), media_type="text/plain", status_code=status.HTTP_200_OK)

    logger.warning("[WhatsApp Webhook] Verification failed: token mismatch or invalid mode.")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification token mismatch"
    )


@router.post("/whatsapp")
async def receive_whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receives real-time delivery status updates from Meta WhatsApp Cloud API:
    - SENT
    - DELIVERED
    - READ
    - FAILED
    Updates corresponding MessageLog records by provider_message_id.
    """
    try:
        data = await request.json()
    except Exception:
        return {"status": "ignored", "reason": "invalid_json"}

    entries = data.get("entry", [])
    updated_count = 0

    for entry in entries:
        for change in entry.get("changes", []):
            val = change.get("value", {})
            statuses = val.get("statuses", [])

            for st in statuses:
                wamid = st.get("id")
                raw_status = st.get("status", "").lower()
                errors = st.get("errors", [])

                if not wamid or not raw_status:
                    continue

                status_map = {
                    "sent": "SENT",
                    "delivered": "DELIVERED",
                    "read": "READ",
                    "failed": "FAILED"
                }
                new_status = status_map.get(raw_status)
                if not new_status:
                    continue

                # Find message log
                log_entry = db.query(MessageLog).filter(MessageLog.provider_message_id == wamid).first()
                if log_entry:
                    log_entry.delivery_status = new_status
                    log_entry.updated_at = datetime.now(timezone.utc)

                    if new_status == "FAILED" and errors:
                        err_title = errors[0].get("title") or errors[0].get("message") or "Unknown error"
                        err_code = errors[0].get("code", "N/A")
                        log_entry.error_message = f"Delivery failed ({err_code}): {err_title}"

                    updated_count += 1

    if updated_count > 0:
        db.commit()
        logger.info(f"[WhatsApp Webhook] Updated delivery status for {updated_count} messages.")

    return {"status": "success", "updated": updated_count}
