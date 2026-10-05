import pytest
from app.services import runbook_service
from app.models.runbook import Runbook
from app import db


def test_create_runbook_with_steps(app, engineer_user):
    with app.app_context():
        data = {
            "title": "Nginx TLS Renewal",
            "description": "Certbot automated renewal checklist",
            "status": "active",
            "steps": [
                {
                    "order": 1,
                    "title": "Check Expiry",
                    "instructions": "certbot certificates",
                    "expectedOutcome": "Validity < 30 days"
                },
                {
                    "order": 2,
                    "title": "Run Renewal",
                    "instructions": "certbot renew --dry-run",
                    "expectedOutcome": "All renewals succeeded"
                }
            ]
        }
        rb = runbook_service.create_runbook(data, engineer_user.id)
        assert rb.id is not None
        assert rb.title == "Nginx TLS Renewal"
        assert len(rb.steps) == 2


def test_create_runbook_validation(app, engineer_user):
    with app.app_context():
        with pytest.raises(runbook_service.RunbookError) as exc_info:
            runbook_service.create_runbook({"title": "", "steps": []}, engineer_user.id)
        assert exc_info.value.status_code == 400


def test_update_runbook(app, engineer_user):
    with app.app_context():
        rb = runbook_service.create_runbook({
            "title": "Original Title",
            "steps": [{"order": 1, "title": "S1", "instructions": "do task", "expectedOutcome": "done"}]
        }, engineer_user.id)

        updated = runbook_service.update_runbook(rb.id, {
            "title": "Updated Title",
            "steps": [
                {"order": 1, "title": "S1 New", "instructions": "new instructions", "expectedOutcome": "ok"}
            ]
        }, engineer_user)
        assert updated.title == "Updated Title"
        assert updated.steps[0].title == "S1 New"


def test_soft_delete_runbook(app, engineer_user):
    with app.app_context():
        rb = runbook_service.create_runbook({
            "title": "To Delete",
            "steps": [{"order": 1, "title": "S1", "instructions": "step", "expectedOutcome": "ok"}]
        }, engineer_user.id)

        deleted = runbook_service.delete_runbook(rb.id, engineer_user)
        assert deleted.status == "inactive"


def test_runbook_versioning(app, engineer_user):
    with app.app_context():
        rb = runbook_service.create_runbook({
            "title": "Base Procedure",
            "steps": [{"order": 1, "title": "S1", "instructions": "step", "expectedOutcome": "ok"}]
        }, engineer_user.id)
        assert rb.version == 1

        # Create version 2
        v2 = runbook_service.create_runbook_version(rb.id, {
            "title": "Base Procedure v2",
            "steps": [
                {"order": 1, "title": "S1", "instructions": "step", "expectedOutcome": "ok"},
                {"order": 2, "title": "S2", "instructions": "verify", "expectedOutcome": "verified"}
            ]
        }, engineer_user)
        assert v2.version == 2
        assert v2.parent_runbook_id == rb.id

        versions = runbook_service.get_runbook_versions(rb.id)
        assert len(versions) >= 2
