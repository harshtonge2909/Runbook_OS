from datetime import datetime
from app import db
from app.models.execution import Execution
from app.models.runbook import Runbook
from app.services.audit_service import create_audit_log


class ExecutionError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def start_execution(runbook_id: int, user_id: int) -> Execution:
    """Start an interactive runbook execution, snapshotting current step definitions."""
    runbook = db.session.get(Runbook, runbook_id)
    if not runbook:
        raise ExecutionError("Runbook not found", 404)

    steps_snapshot = [
        {
            "order": s.order,
            "title": s.title,
            "instructions": s.instructions,
            "expectedOutcome": s.expected_outcome or "",
        }
        for s in runbook.steps
    ]

    execution = Execution(
        runbook_id=runbook.id,
        version=runbook.version,
        started_by_id=user_id,
        status="Running",
        current_step=0,
        steps_snapshot=steps_snapshot,
        started_at=datetime.utcnow()
    )
    db.session.add(execution)
    db.session.commit()

    create_audit_log(
        user_id=user_id,
        action="EXECUTION_STARTED",
        resource_type="Execution",
        resource_id=execution.id,
        details=f"Started execution #{execution.id} of runbook '{runbook.title}' (v{runbook.version})"
    )

    return execution


def get_execution_by_id(execution_id: int) -> Execution:
    """Retrieve execution by ID."""
    execution = db.session.get(Execution, execution_id)
    if not execution:
        raise ExecutionError("Execution not found", 404)
    return execution


def move_to_next_step(execution_id: int, user_id: int = None) -> Execution:
    """Advance execution to next step. Completes execution if last step was finished."""
    execution = get_execution_by_id(execution_id)

    if execution.status == "Completed":
        raise ExecutionError("Execution is already completed", 400)

    total_steps = len(execution.steps_snapshot or [])
    execution.current_step += 1

    if execution.current_step >= total_steps:
        execution.status = "Completed"
        execution.completed_at = datetime.utcnow()
        create_audit_log(
            user_id=user_id or execution.started_by_id,
            action="EXECUTION_COMPLETED",
            resource_type="Execution",
            resource_id=execution.id,
            details=f"Completed execution #{execution.id} after step {total_steps}"
        )

    db.session.commit()
    return execution


def complete_execution(execution_id: int, user_id: int = None) -> Execution:
    """Explicitly mark execution as completed."""
    execution = get_execution_by_id(execution_id)

    if execution.status == "Completed":
        raise ExecutionError("Execution is already completed", 400)

    execution.status = "Completed"
    execution.completed_at = datetime.utcnow()
    db.session.commit()

    create_audit_log(
        user_id=user_id or execution.started_by_id,
        action="EXECUTION_COMPLETED",
        resource_type="Execution",
        resource_id=execution.id,
        details=f"Finished execution #{execution.id}"
    )

    return execution


def list_executions(page: int = 1, limit: int = 20):
    """Retrieve paginated executions ordered by start time descending."""
    pagination = Execution.query.order_by(Execution.started_at.desc()).paginate(
        page=page,
        per_page=limit,
        error_out=False
    )
    return pagination
