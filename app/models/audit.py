from datetime import datetime
from app import db


class AuditLog(db.Model):
    """Immutable audit trail for operational events."""
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    resource_type = db.Column(db.String(50), nullable=False, index=True)
    resource_id = db.Column(db.String(100), nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationship
    user = db.relationship("User", backref=db.backref("audit_logs", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "_id": str(self.id),  # Compatibility
            "user": {
                "id": self.user.id,
                "_id": str(self.user.id),
                "name": self.user.name,
                "email": self.user.email,
            } if self.user else None,
            "action": self.action,
            "resourceType": self.resource_type,
            "resourceId": self.resource_id,
            "details": self.details,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action} on {self.resource_type}#{self.resource_id}>"
