import os
import pytest
from app import create_app, db
from app.models.user import User
from app.models.runbook import Runbook, Step
from app.models.execution import Execution
from app.models.audit import AuditLog
from app.services.auth_service import generate_jwt_token


@pytest.fixture(scope="session")
def app():
    """Application fixture configured for testing."""
    os.environ["FLASK_ENV"] = "testing"
    app = create_app("testing")
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()


@pytest.fixture(scope="function")
def client(app):
    """Test HTTP client."""
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def db_session(app):
    """Provide a clean database session per test function."""
    with app.app_context():
        # Start a nested transaction
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Configure session to use this transaction
        session = db.session
        
        yield session

        transaction.rollback()
        connection.close()
        session.remove()


@pytest.fixture
def admin_user(app):
    """Create and return a test admin user."""
    with app.app_context():
        user = User.query.filter_by(email="testadmin@runbookos.dev").first()
        if not user:
            user = User(
                name="Test Admin",
                email="testadmin@runbookos.dev",
                role="Admin",
                status="active"
            )
            user.set_password("AdminPass123!")
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def engineer_user(app):
    """Create and return a test engineer user."""
    with app.app_context():
        user = User.query.filter_by(email="testengineer@runbookos.dev").first()
        if not user:
            user = User(
                name="Test Engineer",
                email="testengineer@runbookos.dev",
                role="Engineer",
                status="active"
            )
            user.set_password("EngineerPass123!")
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def admin_token(app, admin_user):
    """Generate JWT Bearer token for admin."""
    with app.app_context():
        user = db.session.get(User, admin_user.id)
        return generate_jwt_token(user)


@pytest.fixture
def engineer_token(app, engineer_user):
    """Generate JWT Bearer token for engineer."""
    with app.app_context():
        user = db.session.get(User, engineer_user.id)
        return generate_jwt_token(user)
