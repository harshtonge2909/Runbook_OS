import functools
from flask import Blueprint, jsonify, request, session, g
from app import db
from app.models.user import User
from app.services import auth_service, runbook_service, execution_service, audit_service, dashboard_service, ai_service

api_bp = Blueprint("api", __name__)


def api_authenticate(f):
    """Decorator to authenticate API requests via Bearer token or active Session."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        user = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = auth_service.decode_jwt_token(token)
                user = db.session.get(User, payload["userId"])
            except auth_service.AuthError as e:
                return jsonify({"success": False, "message": str(e)}), e.status_code
        elif "user_id" in session:
            user = db.session.get(User, session["user_id"])

        if not user:
            return jsonify({"success": False, "message": "Authentication required"}), 401
        
        if not user.is_active:
            return jsonify({"success": False, "message": "User account is inactive"}), 403

        g.current_user = user
        return f(*args, **kwargs)
    return decorated


# ==========================================
# AUTH ENDPOINTS
# ==========================================

@api_bp.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    try:
        user = auth_service.register_user(
            name=data.get("name", ""),
            email=data.get("email", ""),
            password=data.get("password", ""),
            role=data.get("role", "Engineer")
        )
        return jsonify({
            "success": True,
            "message": "User registered successfully",
            "data": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role
            }
        }), 201
    except auth_service.AuthError as e:
        return jsonify({"success": False, "message": e.message}), e.status_code


@api_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    try:
        user = auth_service.authenticate_user(
            email=data.get("email", ""),
            password=data.get("password", "")
        )
        token = auth_service.generate_jwt_token(user)
        # Also establish session for browser-based fetch calls
        session["user_id"] = user.id
        return jsonify({
            "success": True,
            "message": "Login successful",
            "data": {
                "token": token,
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role
                }
            }
        }), 200
    except auth_service.AuthError as e:
        return jsonify({"success": False, "message": e.message}), e.status_code


@api_bp.route("/auth/me", methods=["GET"])
@api_authenticate
def get_current_user():
    return jsonify({
        "success": True,
        "data": g.current_user.to_dict()
    })


# ==========================================
# RUNBOOK ENDPOINTS
# ==========================================

@api_bp.route("/runbooks", methods=["GET"])
@api_authenticate
def get_runbooks():
    search = request.args.get("search") or request.args.get("title")
    status = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)

    result = runbook_service.get_all_runbooks(search=search, status=status, page=page, limit=limit)
    return jsonify({
        "success": True,
        "data": {
            "runbooks": [rb.to_dict(include_steps=True) for rb in result["runbooks"]],
            "pagination": {
                "total": result["total"],
                "page": result["page"],
                "limit": result["limit"],
                "totalPages": result["totalPages"]
            }
        }
    }), 200


@api_bp.route("/runbooks", methods=["POST"])
@api_authenticate
def create_runbook():
    data = request.get_json() or {}
    try:
        runbook = runbook_service.create_runbook(data, g.current_user.id)
        return jsonify({
            "success": True,
            "message": "Runbook created successfully",
            "data": runbook.to_dict(include_steps=True)
        }), 201
    except runbook_service.RunbookError as e:
        return jsonify({"success": False, "message": e.message}), e.status_code


@api_bp.route("/runbooks/<int:id>", methods=["GET"])
@api_authenticate
def get_runbook(id):
    try:
        runbook = runbook_service.get_runbook_by_id(id)
        return jsonify({
            "success": True,
            "data": runbook.to_dict(include_steps=True)
        }), 200
    except runbook_service.RunbookError as e:
        return jsonify({"success": False, "message": e.message}), e.status_code


@api_bp.route("/runbooks/<int:id>", methods=["PUT"])
@api_authenticate
def update_runbook(id):
    data = request.get_json() or {}
    try:
        runbook = runbook_service.update_runbook(id, data, g.current_user)
        return jsonify({
            "success": True,
            "message": "Runbook updated successfully",
            "data": runbook.to_dict(include_steps=True)
        }), 200
    except runbook_service.RunbookError as e:
        return jsonify({"success": False, "message": e.message}), e.status_code


@api_bp.route("/runbooks/<int:id>", methods=["DELETE"])
@api_authenticate
def delete_runbook(id):
    try:
        runbook_service.delete_runbook(id, g.current_user)
        return jsonify({
            "success": True,
            "message": "Runbook deleted successfully"
        }), 200
    except runbook_service.RunbookError as e:
        return jsonify({"success": False, "message": e.message}), e.status_code


@api_bp.route("/runbooks/<int:id>/version", methods=["POST"])
@api_authenticate
def create_version(id):
    data = request.get_json() or {}
    try:
        new_version = runbook_service.create_runbook_version(id, data, g.current_user)
        return jsonify({
            "success": True,
            "message": "New runbook version created successfully",
            "data": new_version.to_dict(include_steps=True)
        }), 201
    except runbook_service.RunbookError as e:
        return jsonify({"success": False, "message": e.message}), e.status_code


@api_bp.route("/runbooks/<int:id>/versions", methods=["GET"])
@api_authenticate
def get_versions(id):
    try:
        versions = runbook_service.get_runbook_versions(id)
        return jsonify({
            "success": True,
            "data": [v.to_dict(include_steps=False) for v in versions]
        }), 200
    except runbook_service.RunbookError as e:
        return jsonify({"success": False, "message": e.message}), e.status_code


# ==========================================
# EXECUTION ENDPOINTS
# ==========================================

@api_bp.route("/executions/<int:runbook_id>/start", methods=["POST"])
@api_authenticate
def start_execution(runbook_id):
    try:
        execution = execution_service.start_execution(runbook_id, g.current_user.id)
        return jsonify({
            "success": True,
            "message": "Execution started successfully",
            "data": execution.to_dict()
        }), 201
    except execution_service.ExecutionError as e:
        return jsonify({"success": False, "message": e.message}), e.status_code


@api_bp.route("/executions/<int:execution_id>", methods=["GET"])
@api_authenticate
def get_execution(execution_id):
    try:
        execution = execution_service.get_execution_by_id(execution_id)
        return jsonify({
            "success": True,
            "data": execution.to_dict()
        }), 200
    except execution_service.ExecutionError as e:
        return jsonify({"success": False, "message": e.message}), e.status_code


@api_bp.route("/executions/<int:execution_id>/next", methods=["POST"])
@api_authenticate
def next_step(execution_id):
    try:
        execution = execution_service.move_to_next_step(execution_id, g.current_user.id)
        return jsonify({
            "success": True,
            "message": "Moved to next step successfully",
            "data": execution.to_dict()
        }), 200
    except execution_service.ExecutionError as e:
        return jsonify({"success": False, "message": e.message}), e.status_code


@api_bp.route("/executions/<int:execution_id>/complete", methods=["POST"])
@api_authenticate
def complete_execution(execution_id):
    try:
        execution = execution_service.complete_execution(execution_id, g.current_user.id)
        return jsonify({
            "success": True,
            "message": "Execution completed successfully",
            "data": execution.to_dict()
        }), 200
    except execution_service.ExecutionError as e:
        return jsonify({"success": False, "message": e.message}), e.status_code


# ==========================================
# DASHBOARD & AUDIT ENDPOINTS
# ==========================================

@api_bp.route("/dashboard/stats", methods=["GET"])
@api_authenticate
def get_dashboard_stats():
    stats = dashboard_service.get_dashboard_stats()
    return jsonify({
        "success": True,
        "data": stats
    }), 200


@api_bp.route("/audit", methods=["GET"])
@api_authenticate
def get_audit_logs():
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 50, type=int)
    pagination = audit_service.get_audit_logs(limit=limit, page=page)
    return jsonify({
        "success": True,
        "data": [log.to_dict() for log in pagination.items],
        "pagination": {
            "total": pagination.total,
            "page": pagination.page,
            "limit": pagination.per_page,
            "totalPages": pagination.pages
        }
    }), 200


# ==========================================
# GROQ AI ENDPOINTS (Optional: Only if GROQ_API_KEY configured)
# ==========================================

@api_bp.route("/ai/status", methods=["GET"])
@api_authenticate
def ai_status():
    available = ai_service.is_ai_available()
    return jsonify({
        "success": True,
        "available": available,
        "model": "llama-3.3-70b-versatile" if available else None,
        "message": "Groq AI is ready" if available else "GROQ_API_KEY is not configured"
    }), 200


@api_bp.route("/ai/generate-runbook", methods=["POST"])
@api_authenticate
def ai_generate_runbook():
    if not ai_service.is_ai_available():
        return jsonify({
            "success": False,
            "message": "Groq AI is not configured. Set GROQ_API_KEY in .env to enable AI runbook generation."
        }), 503

    data = request.get_json() or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"success": False, "message": "Prompt is required to generate a runbook"}), 400

    result = ai_service.generate_runbook_from_prompt(prompt)
    status_code = 200 if result.get("success") else 500
    return jsonify(result), status_code


@api_bp.route("/ai/troubleshoot", methods=["POST"])
@api_authenticate
def ai_troubleshoot():
    if not ai_service.is_ai_available():
        return jsonify({
            "success": False,
            "message": "Groq AI is not configured. Set GROQ_API_KEY in .env to enable AI troubleshooting."
        }), 503

    data = request.get_json() or {}
    step_title = data.get("stepTitle", "")
    instructions = data.get("instructions", "")
    expected = data.get("expectedOutcome", "")
    user_observation = data.get("observation", "")

    result = ai_service.troubleshoot_step(step_title, instructions, expected, user_observation)
    status_code = 200 if result.get("success") else 500
    return jsonify(result), status_code
