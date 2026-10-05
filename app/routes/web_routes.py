import functools
import json
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    session, g, abort, current_app
)
from app import db
from app.models.user import User
from app.models.runbook import Runbook, Step
from app.models.execution import Execution
from app.forms.auth_forms import LoginForm, RegisterForm
from app.forms.runbook_forms import RunbookForm, VersionForm
from app.services import (
    auth_service, runbook_service, execution_service,
    audit_service, dashboard_service, ai_service
)

web_bp = Blueprint("web", __name__)


def login_required(f):
    """Decorator requiring active session authentication for web pages."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("web.login", next=request.path))
        user = db.session.get(User, user_id)
        if not user or not user.is_active:
            session.clear()
            flash("Your session is invalid or your account is deactivated.", "danger")
            return redirect(url_for("web.login"))
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@web_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("web.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = auth_service.authenticate_user(
                email=form.email.data,
                password=form.password.data
            )
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_role"] = user.role
            flash(f"Welcome back, {user.name}!", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("web.dashboard"))
        except auth_service.AuthError as e:
            flash(e.message, "danger")

    return render_template("auth/login.html", form=form)


@web_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("web.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = auth_service.register_user(
                name=form.name.data,
                email=form.email.data,
                password=form.password.data,
                role=form.role.data
            )
            flash("Account registered successfully! Please sign in.", "success")
            return redirect(url_for("web.login"))
        except auth_service.AuthError as e:
            flash(e.message, "danger")

    return render_template("auth/register.html", form=form)


@web_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("web.login"))


# ==========================================
# DASHBOARD
# ==========================================

@web_bp.route("/")
@web_bp.route("/dashboard")
@login_required
def dashboard():
    stats = dashboard_service.get_dashboard_stats()
    recent_runbooks = Runbook.query.filter_by(status="active").order_by(Runbook.created_at.desc()).limit(5).all()
    recent_executions = Execution.query.order_by(Execution.started_at.desc()).limit(5).all()
    return render_template(
        "dashboard/index.html",
        stats=stats,
        recent_runbooks=recent_runbooks,
        recent_executions=recent_executions
    )


# ==========================================
# RUNBOOKS
# ==========================================

@web_bp.route("/runbooks")
@login_required
def runbook_list():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)

    result = runbook_service.get_all_runbooks(
        search=search,
        status=status,
        page=page,
        limit=10
    )
    return render_template(
        "runbooks/list.html",
        runbooks=result["runbooks"],
        total=result["total"],
        page=result["page"],
        total_pages=result["totalPages"],
        search=search,
        status=status
    )


@web_bp.route("/runbooks/create", methods=["GET", "POST"])
@login_required
def create_runbook():
    form = RunbookForm()
    if form.validate_on_submit():
        steps_json = form.steps_json.data or "[]"
        try:
            steps = json.loads(steps_json)
        except Exception:
            steps = []

        # If no json parsed, check form data
        if not steps:
            # Parse from standard form step inputs
            step_titles = request.form.getlist("step_title[]")
            step_instructions = request.form.getlist("step_instructions[]")
            step_expected = request.form.getlist("step_expected[]")
            for i in range(len(step_titles)):
                if step_instructions[i].strip():
                    steps.append({
                        "order": i + 1,
                        "title": step_titles[i].strip(),
                        "instructions": step_instructions[i].strip(),
                        "expectedOutcome": step_expected[i].strip() if i < len(step_expected) else ""
                    })

        try:
            runbook = runbook_service.create_runbook({
                "title": form.title.data,
                "description": form.description.data,
                "status": form.status.data,
                "steps": steps
            }, g.current_user.id)
            flash(f"Runbook '{runbook.title}' created successfully!", "success")
            return redirect(url_for("web.runbook_details", id=runbook.id))
        except runbook_service.RunbookError as e:
            flash(e.message, "danger")

    return render_template("runbooks/create.html", form=form)


@web_bp.route("/runbooks/<int:id>")
@login_required
def runbook_details(id):
    try:
        runbook = runbook_service.get_runbook_by_id(id)
    except runbook_service.RunbookError:
        abort(404)
    return render_template("runbooks/details.html", runbook=runbook)


@web_bp.route("/runbooks/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_runbook(id):
    try:
        runbook = runbook_service.get_runbook_by_id(id)
    except runbook_service.RunbookError:
        abort(404)

    is_owner = (runbook.created_by_id == g.current_user.id)
    is_admin = g.current_user.is_admin
    if not is_owner and not is_admin:
        flash("You are not authorized to edit this runbook.", "danger")
        return redirect(url_for("web.runbook_details", id=runbook.id))

    form = RunbookForm(obj=runbook)
    if form.validate_on_submit():
        steps_json = form.steps_json.data or "[]"
        try:
            steps = json.loads(steps_json)
        except Exception:
            steps = []

        if not steps:
            step_titles = request.form.getlist("step_title[]")
            step_instructions = request.form.getlist("step_instructions[]")
            step_expected = request.form.getlist("step_expected[]")
            for i in range(len(step_titles)):
                if step_instructions[i].strip():
                    steps.append({
                        "order": i + 1,
                        "title": step_titles[i].strip(),
                        "instructions": step_instructions[i].strip(),
                        "expectedOutcome": step_expected[i].strip() if i < len(step_expected) else ""
                    })

        try:
            runbook_service.update_runbook(id, {
                "title": form.title.data,
                "description": form.description.data,
                "status": form.status.data,
                "steps": steps
            }, g.current_user)
            flash("Runbook updated successfully!", "success")
            return redirect(url_for("web.runbook_details", id=id))
        except runbook_service.RunbookError as e:
            flash(e.message, "danger")

    return render_template("runbooks/edit.html", form=form, runbook=runbook)


@web_bp.route("/runbooks/<int:id>/delete", methods=["POST"])
@login_required
def delete_runbook(id):
    try:
        runbook_service.delete_runbook(id, g.current_user)
        flash("Runbook deleted successfully.", "success")
    except runbook_service.RunbookError as e:
        flash(e.message, "danger")
    return redirect(url_for("web.runbook_list"))


@web_bp.route("/runbooks/<int:id>/versions")
@login_required
def runbook_versions(id):
    try:
        runbook = runbook_service.get_runbook_by_id(id)
        versions = runbook_service.get_runbook_versions(id)
    except runbook_service.RunbookError:
        abort(404)
    return render_template("runbooks/versions.html", runbook=runbook, versions=versions)


@web_bp.route("/runbooks/<int:id>/create-version", methods=["POST"])
@login_required
def create_version(id):
    try:
        runbook = runbook_service.get_runbook_by_id(id)
        new_version = runbook_service.create_runbook_version(id, {
            "title": runbook.title,
            "description": runbook.description,
            "steps": [s.to_dict() for s in runbook.steps]
        }, g.current_user)
        flash(f"New version v{new_version.version} created!", "success")
        return redirect(url_for("web.runbook_details", id=new_version.id))
    except runbook_service.RunbookError as e:
        flash(e.message, "danger")
        return redirect(url_for("web.runbook_versions", id=id))


# ==========================================
# EXECUTIONS
# ==========================================

@web_bp.route("/runbooks/<int:id>/execute", methods=["POST"])
@login_required
def execute_runbook(id):
    try:
        execution = execution_service.start_execution(id, g.current_user.id)
        flash(f"Execution started for '{execution.runbook.title}'.", "info")
        return redirect(url_for("web.execution_runner", execution_id=execution.id))
    except execution_service.ExecutionError as e:
        flash(e.message, "danger")
        return redirect(url_for("web.runbook_details", id=id))


@web_bp.route("/executions/<int:execution_id>")
@login_required
def execution_runner(execution_id):
    try:
        execution = execution_service.get_execution_by_id(execution_id)
    except execution_service.ExecutionError:
        abort(404)

    steps = execution.steps_snapshot or []
    total_steps = len(steps)
    current_idx = min(execution.current_step, max(0, total_steps - 1))
    current_step = steps[current_idx] if steps else None

    # Calculate progress
    if total_steps == 0:
        progress_pct = 0
    elif execution.status == "Completed":
        progress_pct = 100
    else:
        progress_pct = round(((current_idx + 1) / total_steps) * 100)

    return render_template(
        "executions/runner.html",
        execution=execution,
        runbook=execution.runbook,
        steps=steps,
        total_steps=total_steps,
        current_idx=current_idx,
        current_step=current_step,
        progress_pct=progress_pct,
        is_last_step=(current_idx == total_steps - 1)
    )


@web_bp.route("/executions")
@login_required
def execution_list():
    page = request.args.get("page", 1, type=int)
    pagination = execution_service.list_executions(page=page, limit=15)
    return render_template(
        "executions/list.html",
        executions=pagination.items,
        pagination=pagination
    )


# ==========================================
# AUDIT LOGS
# ==========================================

@web_bp.route("/audit")
@login_required
def audit_logs():
    page = request.args.get("page", 1, type=int)
    pagination = audit_service.get_audit_logs(limit=25, page=page)
    return render_template(
        "audit/list.html",
        logs=pagination.items,
        pagination=pagination
    )
