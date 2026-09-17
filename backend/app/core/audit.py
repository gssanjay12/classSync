import json
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from app.models.audit import AuditLog

def record_audit_log(
    db: Session,
    action: str,
    target_type: str,
    actor_user_id: Optional[int] = None,
    target_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    # Ensure sensitive fields (passwords, tokens) are never recorded
    safe_metadata = {}
    if metadata:
        for k, v in metadata.items():
            if any(forbidden in k.lower() for forbidden in ["password", "token", "hash", "secret"]):
                continue
            safe_metadata[k] = v

    log_entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        metadata_json=json.dumps(safe_metadata) if safe_metadata else None,
        ip_address=ip_address
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
