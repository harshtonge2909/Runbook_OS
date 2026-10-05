from app import db
from app.models.audit import AuditLog


def create_audit_log(user_id, action, resource_type, resource_id=None, details=None):
    """Create an immutable audit log entry."""
    try:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            details=details
        )
        db.session.add(log)
        db.session.commit()
        return log
    except Exception as e:
        db.session.rollback()
        # Logging failure should not break main flow
        return None


def get_audit_logs(limit=100, page=1):
    """Retrieve audit logs ordered by creation time descending."""
    pagination = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(
        page=page,
        per_page=limit,
        error_out=False
    )
    return pagination
