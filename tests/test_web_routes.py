import re
import pytest
from app import create_app, db
from app.models.user import User
from app.models.runbook import Runbook, Step
from app.models.execution import Execution


@pytest.fixture
def csrf_client():
    """Client with CSRF enabled to test CSRF protection."""
    app = create_app("testing")
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["TESTING"] = True
    with app.app_context():
        yield app.test_client()


def test_login_page_renders_with_csrf(csrf_client):
    res = csrf_client.get("/login")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'name="csrf_token"' in html
    assert "Operator Sign In" in html


def test_login_post_without_csrf_is_rejected(csrf_client):
    res = csrf_client.post("/login", data={
        "email": "admin@runbookos.dev",
        "password": "Admin@123456"
    })
    # CSRF failure should return 400 Bad Request
    assert res.status_code == 400


def test_dashboard_redirects_unauthenticated(client):
    res = client.get("/dashboard")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]


def test_authenticated_user_accesses_dashboard(client, app, admin_user):
    with client.session_transaction() as sess:
        sess["user_id"] = admin_user.id

    res = client.get("/dashboard")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Operational Dashboard" in html
    assert "Total Runbooks" in html


def test_runbook_create_page_renders(client, app, engineer_user):
    with client.session_transaction() as sess:
        sess["user_id"] = engineer_user.id

    res = client.get("/runbooks/create")
    assert res.status_code == 200
    assert "Create Runbook" in res.get_data(as_text=True)


def test_execution_runner_page_renders(client, app, engineer_user):
    with app.app_context():
        rb = Runbook(
            title="Web Runner Test",
            created_by_id=engineer_user.id
        )
        db.session.add(rb)
        db.session.flush()

        step = Step(runbook_id=rb.id, order=1, title="S1", instructions="hostname", expected_outcome="host")
        db.session.add(step)

        ex = Execution(
            runbook_id=rb.id,
            version=1,
            started_by_id=engineer_user.id,
            steps_snapshot=[step.to_dict()]
        )
        db.session.add(ex)
        db.session.commit()
        ex_id = ex.id

    with client.session_transaction() as sess:
        sess["user_id"] = engineer_user.id

    res = client.get(f"/executions/{ex_id}")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert f"Execution #{ex_id}" in html
    assert "Operational Instructions" in html
    assert "hostname" in html


def test_audit_logs_page_renders(client, app, admin_user):
    with client.session_transaction() as sess:
        sess["user_id"] = admin_user.id

    res = client.get("/audit")
    assert res.status_code == 200
    assert "Operational Audit Trail" in res.get_data(as_text=True)
