from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(db.Model):
    """User model with role-based access control (Admin, Engineer)."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="Engineer", nullable=False)  # Admin or Engineer
    status = db.Column(db.String(20), default="active", nullable=False)  # active or inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "active")
        kwargs.setdefault("role", "Engineer")
        super().__init__(**kwargs)

    def set_password(self, password: str):
        """Hash password using Werkzeug."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password hash using Werkzeug."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "Admin"

    @property
    def is_active(self) -> bool:
        return (self.status or "active") == "active"

    def to_dict(self):
        return {
            "id": self.id,
            "_id": str(self.id),  # Compatibility with previous API format
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "status": self.status,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
