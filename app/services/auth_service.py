from datetime import datetime, timezone
import jwt
from flask import current_app
from app import db
from app.models.user import User


class AuthError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register_user(name: str, email: str, password: str, role: str = "Engineer") -> User:
    """Register a new user with hashed password."""
    email_clean = email.strip().lower()
    
    if User.query.filter_by(email=email_clean).first():
        raise AuthError("Email already registered", 409)

    user = User(
        name=name.strip(),
        email=email_clean,
        role=role if role in ["Admin", "Engineer"] else "Engineer",
        status="active"
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(email: str, password: str) -> User:
    """Authenticate user credentials."""
    email_clean = email.strip().lower()
    user = User.query.filter_by(email=email_clean).first()

    if not user or not user.check_password(password):
        raise AuthError("Invalid email or password", 401)

    if not user.is_active:
        raise AuthError("Account is inactive", 403)

    return user


def generate_jwt_token(user: User) -> str:
    """Generate a JWT token for REST API calls."""
    secret_key = current_app.config["JWT_SECRET_KEY"]
    expires = datetime.now(timezone.utc) + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]

    payload = {
        "userId": user.id,
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "exp": expires
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_jwt_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    secret_key = current_app.config["JWT_SECRET_KEY"]
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired", 401)
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token", 401)
