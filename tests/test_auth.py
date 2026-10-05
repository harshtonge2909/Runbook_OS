import pytest
from app.services import auth_service
from app.models.user import User
from app import db


import uuid


def test_user_registration_success(app):
    with app.app_context():
        email = f"operator_{uuid.uuid4().hex[:8]}@runbookos.dev"
        user = auth_service.register_user(
            name="New Operator",
            email=email,
            password="Password123!",
            role="Engineer"
        )
        assert user.id is not None
        assert user.email == email
        assert user.role == "Engineer"


def test_user_registration_duplicate_email(app):
    with app.app_context():
        email = f"dup_{uuid.uuid4().hex[:8]}@runbookos.dev"
        auth_service.register_user(
            name="First",
            email=email,
            password="Password123!"
        )
        with pytest.raises(auth_service.AuthError) as exc_info:
            auth_service.register_user(
                name="Second",
                email=email,
                password="Password456!"
            )
        assert exc_info.value.status_code == 409


def test_user_authentication_success(app):
    with app.app_context():
        email = f"auth_ok_{uuid.uuid4().hex[:8]}@runbookos.dev"
        auth_service.register_user(name="Auth Tester", email=email, password="ValidPassword123")
        user = auth_service.authenticate_user(email, "ValidPassword123")
        assert user.email == email


def test_user_authentication_invalid_password(app):
    with app.app_context():
        email = f"auth_fail_{uuid.uuid4().hex[:8]}@runbookos.dev"
        auth_service.register_user(name="Fail Tester", email=email, password="ValidPassword123")
        with pytest.raises(auth_service.AuthError) as exc_info:
            auth_service.authenticate_user(email, "WrongPassword")
        assert exc_info.value.status_code == 401


def test_jwt_generation_and_decoding(app, engineer_user):
    with app.app_context():
        token = auth_service.generate_jwt_token(engineer_user)
        assert isinstance(token, str)
        payload = auth_service.decode_jwt_token(token)
        assert payload["userId"] == engineer_user.id
        assert payload["email"] == engineer_user.email
