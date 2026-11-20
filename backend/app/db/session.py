"""
Database connection, engine configuration, and session management.

Supports PostgreSQL via psycopg (and SQLite for local testing/development).
Credentials are read exclusively from environment variables and never logged or exposed.
"""

import os
from contextlib import contextmanager
from typing import Generator, Optional, Tuple

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

# Load .env file if present
load_dotenv()

# Resolve absolute path to data directory inside backend folder
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DEFAULT_DB_PATH = os.path.join(DATA_DIR, "financial_portfolio.db").replace(os.sep, "/")
DEFAULT_DB_URL = f"sqlite:///{DEFAULT_DB_PATH}"


def get_database_url() -> str:
    """Return the configured DATABASE_URL from environment or fallback default.

    Returns:
        Clean database URL string.
    """
    url = os.getenv("DATABASE_URL")
    if not url or not url.strip():
        return DEFAULT_DB_URL
    url_clean = url.strip()
    if url_clean.startswith("sqlite:///./"):
        # Resolve relative sqlite path to absolute backend path
        rel_sub = url_clean.replace("sqlite:///./", "")
        abs_p = os.path.join(BACKEND_DIR, rel_sub).replace(os.sep, "/")
        return f"sqlite:///{abs_p}"
    return url_clean


def mask_database_url(url: str) -> str:
    """Return a masked representation of a database URL hiding credentials.

    Args:
        url: Full database connection string.

    Returns:
        Safe string with password obscured, e.g. postgresql+psycopg://user:***@localhost:5432/db
    """
    if "@" in url and "://" in url:
        try:
            proto, rest = url.split("://", 1)
            auth, host_path = rest.split("@", 1)
            if ":" in auth:
                user, _ = auth.split(":", 1)
                return f"{proto}://{user}:***@{host_path}"
            return f"{proto}://***@{host_path}"
        except Exception:
            return "***masked-database-url***"
    return url


def create_db_engine(url: Optional[str] = None) -> Engine:
    """Create and return a configured SQLAlchemy Engine.

    Args:
        url: Database URL. If None, loaded via get_database_url().

    Returns:
        SQLAlchemy Engine instance.
    """
    db_url = url or get_database_url()
    connect_args = {}

    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        return create_engine(
            db_url,
            connect_args=connect_args,
            pool_pre_ping=True,
            echo=False,
        )

    # PostgreSQL configuration
    return create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
        echo=False,
    )


# Module-level default engine and SessionLocal factory
engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a managed SQLAlchemy database session.

    Ensures the session is cleanly closed upon request completion or exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for standalone scripts or tasks needing a database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection(target_engine: Optional[Engine] = None) -> Tuple[bool, str]:
    """Verify database connectivity without leaking sensitive connection details.

    Args:
        target_engine: Optional engine to test. If None, default module engine is tested.

    Returns:
        Tuple of (is_connected: bool, safe_message: str).
    """
    eng = target_engine or engine
    safe_url = mask_database_url(str(eng.url))
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, f"Successfully connected to {safe_url}"
    except SQLAlchemyError as exc:
        # Provide diagnostic error message without leaking sensitive credentials
        return False, f"Failed to connect to {safe_url}: {type(exc).__name__}"
    except Exception as exc:
        return False, f"Unexpected error connecting to {safe_url}: {type(exc).__name__}"
