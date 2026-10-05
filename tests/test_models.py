from app.models.user import User
from app.models.runbook import Runbook, Step
from app.models.execution import Execution
from app.models.audit import AuditLog
from app import db


def test_user_password_hashing(app):
    with app.app_context():
        user = User(name="Security Tester", email="hash@runbookos.dev", role="Engineer")
        user.set_password("MySecurePass#2026")
        
        assert user.password_hash != "MySecurePass#2026"
        assert user.check_password("MySecurePass#2026") is True
        assert user.check_password("WrongPassword") is False


def test_user_role_properties(app):
    with app.app_context():
        admin = User(name="Admin User", email="admin_prop@runbookos.dev", role="Admin")
        engineer = User(name="Eng User", email="eng_prop@runbookos.dev", role="Engineer")
        
        assert admin.is_admin is True
        assert engineer.is_admin is False
        assert admin.is_active is True


def test_runbook_and_step_relationship(app, engineer_user):
    with app.app_context():
        rb = Runbook(
            title="Model Test Runbook",
            description="Testing steps cascade",
            created_by_id=engineer_user.id
        )
        db.session.add(rb)
        db.session.flush()

        step1 = Step(runbook_id=rb.id, order=1, title="Step 1", instructions="echo 1", expected_outcome="1")
        step2 = Step(runbook_id=rb.id, order=2, title="Step 2", instructions="echo 2", expected_outcome="2")
        db.session.add_all([step1, step2])
        db.session.commit()

        fetched = db.session.get(Runbook, rb.id)
        assert len(fetched.steps) == 2
        assert fetched.steps[0].title == "Step 1"
        assert fetched.steps[1].title == "Step 2"


def test_execution_jsonb_snapshot(app, engineer_user):
    with app.app_context():
        rb = Runbook(title="Execution Model Test", created_by_id=engineer_user.id)
        db.session.add(rb)
        db.session.flush()

        snapshot = [
            {"order": 1, "title": "Check DB", "instructions": "pg_isready", "expectedOutcome": "accepting connections"}
        ]
        execution = Execution(
            runbook_id=rb.id,
            version=1,
            started_by_id=engineer_user.id,
            steps_snapshot=snapshot
        )
        db.session.add(execution)
        db.session.commit()

        fetched = db.session.get(Execution, execution.id)
        assert fetched.steps_snapshot[0]["title"] == "Check DB"
        assert fetched.status == "Running"
        assert fetched.current_step == 0
