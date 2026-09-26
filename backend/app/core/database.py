from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

# ---------------------------------------------------------------------------
# Engine factory — handles both SQLite (dev/test) and PostgreSQL (Supabase)
# ---------------------------------------------------------------------------

def _build_engine():
    db_url = settings.DATABASE_URL

    if db_url.startswith("sqlite"):
        # SQLite: thread-safety flag required by FastAPI's sync endpoints
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            echo=False,
        )

        # Optimise SQLite with WAL mode and foreign key enforcement
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

        return engine

    else:
        # PostgreSQL / Supabase Transaction Pooler
        # pool_pre_ping validates the connection before use (important with PgBouncer)
        # pool_size / max_overflow tuned for Supabase free-tier connection limits
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,  # recycle connections every 30 min
            echo=False,
            # psycopg2 / asyncpg don't need check_same_thread
        )
        return engine


engine = _build_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
