import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "runbookos-default-secret-key-3.12")
    
    # Strictly PostgreSQL
    _raw_db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres@localhost:5432/runbookos"
    ).strip()

    # Cloud PostgreSQL providers (Neon, Supabase, Render, Railway, etc.)
    # often supply 'postgres://' connection URIs.
    # Normalize to 'postgresql://' as required by SQLAlchemy 1.4+ while enforcing strictly PostgreSQL.
    if _raw_db_url.startswith("postgres://"):
        _raw_db_url = _raw_db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = _raw_db_url
    
    # Enforce strictly PostgreSQL
    if not SQLALCHEMY_DATABASE_URI.startswith("postgresql://") and not SQLALCHEMY_DATABASE_URI.startswith("postgresql+psycopg2://"):
        raise ValueError("STRICT REQUIREMENT: Only PostgreSQL is allowed as the application database.")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Flask-WTF / CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # JWT Authentication for REST API
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_EXPIRATION_HOURS", "24")))

    # AI Integration (Groq API + Llama model)
    # Strictly enabled ONLY if GROQ_API_KEY is configured
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip() or None
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    WTF_CSRF_ENABLED = False  # Allows straightforward form testing
    # PostgreSQL for testing (can use test db or default runbookos)
    _test_db_url = os.getenv(
        "TEST_DATABASE_URL",
        os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5432/runbookos")
    ).strip()
    if _test_db_url.startswith("postgres://"):
        _test_db_url = _test_db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _test_db_url


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
