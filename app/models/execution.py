from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from app import db


class Execution(db.Model):
    """Runbook execution instance capturing step progression and snapshot."""
    __tablename__ = "executions"

    id = db.Column(db.Integer, primary_key=True)
    runbook_id = db.Column(db.Integer, db.ForeignKey("runbooks.id", ondelete="CASCADE"), nullable=False, index=True)
    version = db.Column(db.Integer, nullable=False)
    started_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = db.Column(db.String(20), default="Running", nullable=False, index=True)  # Running, Completed, Failed
    current_step = db.Column(db.Integer, default=0, nullable=False)
    
    # Store steps snapshot as native PostgreSQL JSONB
    steps_snapshot = db.Column(JSONB, nullable=False, default=list)

    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    runbook = db.relationship("Runbook", backref=db.backref("executions", lazy="dynamic", cascade="all, delete-orphan"))
    started_by = db.relationship("User", backref=db.backref("executions", lazy="dynamic", cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "_id": str(self.id),  # Compatibility
            "runbook": {
                "id": self.runbook.id,
                "_id": str(self.runbook.id),
                "title": self.runbook.title,
                "description": self.runbook.description or "",
            } if self.runbook else None,
            "version": self.version,
            "startedBy": {
                "id": self.started_by.id,
                "_id": str(self.started_by.id),
                "name": self.started_by.name,
                "email": self.started_by.email,
            } if self.started_by else None,
            "status": self.status,
            "currentStep": self.current_step,
            "stepsSnapshot": self.steps_snapshot or [],
            "startedAt": self.started_at.isoformat() if self.started_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Execution {self.id}: Runbook {self.runbook_id} (Status: {self.status})>"
