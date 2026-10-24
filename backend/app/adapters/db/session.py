import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Normalize DATABASE_URL for Postgres (Heroku/Render/Neon legacy scheme fix)
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Ensure data directory exists if using default SQLite
if db_url.startswith("sqlite"):
    db_path = db_url.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def wait_for_db(max_retries: int = 5, initial_delay: float = 1.0):
    """
    Retry connecting to the database with exponential backoff on cold starts.
    Crucial for serverless PostgreSQL (e.g. Neon) which suspends compute on idle.
    """
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[Database] Connection established successfully (attempt {attempt}).")
            return
        except Exception as exc:
            if attempt == max_retries:
                print(f"[Database] Failed to connect after {max_retries} attempts: {exc}")
                raise
            delay = initial_delay * (2 ** (attempt - 1))
            print(f"[Database] Connection failed (attempt {attempt}/{max_retries}): {exc}. Retrying in {delay:.1f}s...")
            time.sleep(delay)


def run_migrations_and_seed():
    """
    Run Alembic migrations to head, then seed brand content only if database is empty.
    """
    from alembic.config import Config
    from alembic import command

    # Locate alembic.ini
    candidate_paths = [
        os.path.abspath("alembic.ini"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../alembic.ini")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../alembic.ini")),
    ]
    ini_path = next((p for p in candidate_paths if os.path.exists(p)), "alembic.ini")

    script_loc = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../alembic"))
    if not os.path.exists(script_loc):
        script_loc = os.path.abspath("backend/alembic")

    cfg = Config(ini_path)
    cfg.set_main_option("script_location", script_loc)

    try:
        command.upgrade(cfg, "head")
        print("[Database] Alembic migrations applied successfully to head.")
    except Exception as exc:
        print(f"[Database] Note on startup migrations: {exc}")

    # Seed only if database is empty
    from app.adapters.db.models import User
    from app.seed.loader import run_seed

    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            print("[Database] Database is empty. Loading initial brand seed...")
            run_seed(db=db)
            print("[Database] Initial brand seed loaded successfully.")
        else:
            print(f"[Database] Database already initialized ({user_count} users present). Skipping automatic seed.")
    except Exception as exc:
        print(f"[Database] Note on seed check: {exc}")
    finally:
        db.close()
