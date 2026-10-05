import os
from flask import Flask, jsonify, render_template, request, session, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import config_by_name

# Extensions
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_name=None):
    """Application factory for RunbookOS."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Import models so Alembic / SQLAlchemy knows about them
    from app import models

    # Register Blueprints
    from app.routes.web_routes import web_bp
    from app.routes.api_routes import api_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Exempt API blueprint from CSRF when accessing via REST API / Bearer token
    csrf.exempt(api_bp)

    # Context processors for Jinja2 templates
    @app.context_processor
    def inject_global_template_vars():
        from app.models.user import User
        user = None
        user_id = session.get("user_id")
        if user_id:
            user = db.session.get(User, user_id)
        
        # Check Groq AI availability
        groq_configured = bool(app.config.get("GROQ_API_KEY"))
        return {
            "current_user": user,
            "groq_configured": groq_configured,
            "groq_model": app.config.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        }

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "message": "Resource not found"}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "message": "Access forbidden"}), 403
        return render_template("errors/403.html"), 403

    @app.errorhandler(400)
    def bad_request_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "message": str(error)}), 400
        return render_template("errors/400.html", error=error), 400

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "message": "Internal server error"}), 500
        return render_template("errors/500.html"), 500

    return app
