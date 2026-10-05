import math
from app import db
from app.models.runbook import Runbook, Step
from app.services.audit_service import create_audit_log


class RunbookError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def create_runbook(data: dict, user_id: int) -> Runbook:
    """Create a new operational runbook with sequential steps."""
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    status = data.get("status", "active")
    raw_steps = data.get("steps") or []

    if not title:
        raise RunbookError("Runbook title is required", 400)

    if not raw_steps or len(raw_steps) == 0:
        raise RunbookError("A runbook must contain at least one step", 400)

    runbook = Runbook(
        title=title,
        description=description,
        version=1,
        status=status,
        created_by_id=user_id
    )
    db.session.add(runbook)
    db.session.flush()  # Generate runbook.id

    for idx, s in enumerate(raw_steps):
        step_title = (s.get("title") or f"Step {idx + 1}").strip()
        step_instructions = (s.get("instructions") or "").strip()
        step_expected = (s.get("expectedOutcome") or s.get("expected_outcome") or "").strip()

        if not step_instructions:
            raise RunbookError(f"Instructions are required for step {idx + 1}", 400)

        step = Step(
            runbook_id=runbook.id,
            order=s.get("order", idx + 1),
            title=step_title,
            instructions=step_instructions,
            expected_outcome=step_expected
        )
        db.session.add(step)

    db.session.commit()

    create_audit_log(
        user_id=user_id,
        action="RUNBOOK_CREATED",
        resource_type="Runbook",
        resource_id=runbook.id,
        details=f"Created runbook '{runbook.title}' (v1)"
    )

    return runbook


def get_all_runbooks(search: str = None, status: str = None, page: int = 1, limit: int = 10):
    """Retrieve paginated runbooks with optional PostgreSQL ILIKE search and status filter."""
    query = Runbook.query

    if status and status.strip():
        query = query.filter(Runbook.status == status.strip())
    
    if search and search.strip():
        query = query.filter(Runbook.title.ilike(f"%{search.strip()}%"))

    query = query.order_by(Runbook.created_at.desc())

    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    return {
        "runbooks": pagination.items,
        "total": pagination.total,
        "page": pagination.page,
        "limit": pagination.per_page,
        "totalPages": pagination.pages or 1
    }


def get_runbook_by_id(runbook_id: int, active_only: bool = False) -> Runbook:
    """Get single runbook by integer ID."""
    runbook = db.session.get(Runbook, runbook_id)
    if not runbook:
        raise RunbookError("Runbook not found", 404)
    if active_only and runbook.status != "active":
        raise RunbookError("Runbook is inactive", 404)
    return runbook


def update_runbook(runbook_id: int, data: dict, current_user) -> Runbook:
    """Update runbook attributes and steps (Owner or Admin only)."""
    runbook = get_runbook_by_id(runbook_id)

    # Permission check
    is_owner = (runbook.created_by_id == current_user.id)
    is_admin = getattr(current_user, "is_admin", False) or getattr(current_user, "role", "") == "Admin"

    if not is_owner and not is_admin:
        raise RunbookError("You are not authorized to update this runbook", 403)

    if "title" in data:
        runbook.title = data["title"].strip()
    if "description" in data:
        runbook.description = (data["description"] or "").strip()
    if "status" in data:
        runbook.status = data["status"]

    if "steps" in data and data["steps"] is not None:
        raw_steps = data["steps"]
        if not raw_steps or len(raw_steps) == 0:
            raise RunbookError("A runbook must contain at least one step", 400)

        # Clear existing steps and replace
        Step.query.filter_by(runbook_id=runbook.id).delete()
        for idx, s in enumerate(raw_steps):
            step = Step(
                runbook_id=runbook.id,
                order=s.get("order", idx + 1),
                title=(s.get("title") or f"Step {idx + 1}").strip(),
                instructions=(s.get("instructions") or "").strip(),
                expected_outcome=(s.get("expectedOutcome") or s.get("expected_outcome") or "").strip()
            )
            db.session.add(step)

    db.session.commit()

    create_audit_log(
        user_id=current_user.id,
        action="RUNBOOK_UPDATED",
        resource_type="Runbook",
        resource_id=runbook.id,
        details=f"Updated runbook '{runbook.title}'"
    )

    return runbook


def delete_runbook(runbook_id: int, current_user) -> Runbook:
    """Soft delete runbook (sets status to inactive)."""
    runbook = get_runbook_by_id(runbook_id)

    is_owner = (runbook.created_by_id == current_user.id)
    is_admin = getattr(current_user, "is_admin", False) or getattr(current_user, "role", "") == "Admin"

    if not is_owner and not is_admin:
        raise RunbookError("You are not authorized to delete this runbook", 403)

    runbook.status = "inactive"
    db.session.commit()

    create_audit_log(
        user_id=current_user.id,
        action="RUNBOOK_DELETED",
        resource_type="Runbook",
        resource_id=runbook.id,
        details=f"Deactivated runbook '{runbook.title}'"
    )

    return runbook


def create_runbook_version(runbook_id: int, version_data: dict, current_user) -> Runbook:
    """Create a new version of an existing runbook linked via parent_runbook_id."""
    runbook = get_runbook_by_id(runbook_id)

    is_owner = (runbook.created_by_id == current_user.id)
    is_admin = getattr(current_user, "is_admin", False) or getattr(current_user, "role", "") == "Admin"

    if not is_owner and not is_admin:
        raise RunbookError("You are not authorized to create a new version", 403)

    root_id = runbook.parent_runbook_id or runbook.id

    # Determine highest existing version in this lineage
    versions = Runbook.query.filter(
        (Runbook.id == root_id) | (Runbook.parent_runbook_id == root_id)
    ).all()
    max_version = max((v.version for v in versions), default=1)
    next_version = max_version + 1

    title = version_data.get("title") or runbook.title
    description = version_data.get("description", runbook.description)
    raw_steps = version_data.get("steps") or [s.to_dict() for s in runbook.steps]

    new_version_rb = Runbook(
        title=title,
        description=description,
        version=next_version,
        parent_runbook_id=root_id,
        status="active",
        created_by_id=runbook.created_by_id
    )
    db.session.add(new_version_rb)
    db.session.flush()

    for idx, s in enumerate(raw_steps):
        step = Step(
            runbook_id=new_version_rb.id,
            order=s.get("order", idx + 1),
            title=(s.get("title") or f"Step {idx + 1}").strip(),
            instructions=(s.get("instructions") or "").strip(),
            expected_outcome=(s.get("expectedOutcome") or s.get("expected_outcome") or "").strip()
        )
        db.session.add(step)

    db.session.commit()

    create_audit_log(
        user_id=current_user.id,
        action="RUNBOOK_VERSION_CREATED",
        resource_type="Runbook",
        resource_id=new_version_rb.id,
        details=f"Created version v{next_version} for '{new_version_rb.title}'"
    )

    return new_version_rb


def get_runbook_versions(runbook_id: int):
    """Retrieve all versions in the runbook's lineage."""
    runbook = get_runbook_by_id(runbook_id)
    root_id = runbook.parent_runbook_id or runbook.id

    versions = Runbook.query.filter(
        (Runbook.id == root_id) | (Runbook.parent_runbook_id == root_id)
    ).order_by(Runbook.version.asc()).all()

    return versions
