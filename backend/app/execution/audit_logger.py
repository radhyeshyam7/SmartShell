import uuid
from datetime import datetime
from typing import Dict, List, Optional
from backend.app.database.database import get_db
from backend.app.database.models import AuditLogModel

class AuditLogger:
    """Unified audit logger for recording end-to-end intent, safety, planning, execution, and recovery events"""

    def record_event(self, event_type: str, details: Dict, session_id: str = "default-session") -> str:
        """Record structured audit event into database"""
        try:
            db = next(get_db())
            audit_id = f"audit-{uuid.uuid4().hex[:8]}"
            record = AuditLogModel(
                id=audit_id,
                session_id=session_id,
                event_type=event_type,
                details=details,
                created_at=datetime.utcnow()
            )
            db.add(record)
            db.commit()
            return audit_id
        except Exception:
            return ""

    def get_recent_logs(self, limit: int = 50, event_type: Optional[str] = None) -> List[Dict]:
        """Fetch audit log records"""
        try:
            db = next(get_db())
            query = db.query(AuditLogModel)
            if event_type:
                query = query.filter(AuditLogModel.event_type == event_type)
            records = query.order_by(AuditLogModel.created_at.desc()).limit(limit).all()
            return [{
                "id": r.id,
                "session_id": r.session_id,
                "event_type": r.event_type,
                "details": r.details,
                "created_at": str(r.created_at)
            } for r in records]
        except Exception:
            return []

audit_logger = AuditLogger()
