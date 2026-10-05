import pytest
from app.services import runbook_service, execution_service
from app.models.execution import Execution
from app.models.audit import AuditLog
from app import db


def test_execution_lifecycle(app, engineer_user):
    with app.app_context():
        # Setup runbook
        rb = runbook_service.create_runbook({
            "title": "Interactive Execution Test",
            "steps": [
                {"order": 1, "title": "Check Disk", "instructions": "df -h", "expectedOutcome": "< 80%"},
                {"order": 2, "title": "Clear Logs", "instructions": "journalctl --vacuum-time=2d", "expectedOutcome": "reclaimed space"}
            ]
        }, engineer_user.id)

        # 1. Start execution
        ex = execution_service.start_execution(rb.id, engineer_user.id)
        assert ex.status == "Running"
        assert ex.current_step == 0
        assert len(ex.steps_snapshot) == 2
        assert ex.steps_snapshot[0]["title"] == "Check Disk"

        # 2. Advance to step 2
        ex = execution_service.move_to_next_step(ex.id, engineer_user.id)
        assert ex.status == "Running"
        assert ex.current_step == 1

        # 3. Advance past step 2 -> should complete automatically
        ex = execution_service.move_to_next_step(ex.id, engineer_user.id)
        assert ex.status == "Completed"
        assert ex.completed_at is not None

        # Verify audit logs were generated
        logs = AuditLog.query.filter_by(resource_id=str(ex.id)).all()
        assert len(logs) >= 2  # Started and Completed
