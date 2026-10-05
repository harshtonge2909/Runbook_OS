from datetime import datetime
from app import db


class Step(db.Model):
    """Procedural step within a Runbook."""
    __tablename__ = "steps"

    id = db.Column(db.Integer, primary_key=True)
    runbook_id = db.Column(db.Integer, db.ForeignKey("runbooks.id", ondelete="CASCADE"), nullable=False, index=True)
    order = db.Column(db.Integer, nullable=False, default=1)
    title = db.Column(db.String(255), nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    expected_outcome = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "order": self.order,
            "title": self.title,
            "instructions": self.instructions,
            "expectedOutcome": self.expected_outcome or "",
        }

    def __repr__(self):
        return f"<Step {self.order}: {self.title}>"


class Runbook(db.Model):
    """Operational runbook containing ordered procedural steps."""
    __tablename__ = "runbooks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    version = db.Column(db.Integer, default=1, nullable=False)
    parent_runbook_id = db.Column(db.Integer, db.ForeignKey("runbooks.id", ondelete="SET NULL"), nullable=True)
    status = db.Column(db.String(20), default="active", nullable=False, index=True)  # active, inactive
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    created_by = db.relationship("User", backref=db.backref("runbooks", lazy="dynamic", cascade="all, delete-orphan"))
    steps = db.relationship(
        "Step",
        backref="runbook",
        cascade="all, delete-orphan",
        order_by="Step.order",
        lazy="joined"
    )
    parent_runbook = db.relationship(
        "Runbook",
        remote_side=[id],
        backref=db.backref("child_versions", lazy="dynamic")
    )

    def to_dict(self, include_steps=True):
        data = {
            "id": self.id,
            "_id": str(self.id),  # Compatibility
            "title": self.title,
            "description": self.description or "",
            "version": self.version,
            "parentRunbook": str(self.parent_runbook_id) if self.parent_runbook_id else None,
            "status": self.status,
            "createdBy": {
                "id": self.created_by.id,
                "_id": str(self.created_by.id),
                "name": self.created_by.name,
                "email": self.created_by.email,
            } if self.created_by else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_steps:
            data["steps"] = [s.to_dict() for s in self.steps]
        return data

    def __repr__(self):
        return f"<Runbook {self.id}: {self.title} (v{self.version})>"
