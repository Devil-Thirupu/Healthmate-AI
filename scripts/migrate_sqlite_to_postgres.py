#!/usr/bin/env python3
"""
migrate_sqlite_to_postgres.py
=============================
Safely migrates all existing data from healthmate.db (SQLite) to the
Supabase PostgreSQL database configured in the root .env file.

Usage:
    python scripts/migrate_sqlite_to_postgres.py

Safety guarantees:
  - healthmate.db is NEVER modified or deleted by this script
  - All inserts use ON CONFLICT DO NOTHING (idempotent, safe to re-run)
  - Tables are migrated in FK-dependency order
  - A row count summary is printed after each table

Prerequisites:
  1. Set DATABASE_URL in .env to the Supabase PostgreSQL connection string
  2. pip install psycopg2-binary sqlalchemy python-dotenv
  3. Start the FastAPI app once first (so create_all runs and tables exist in PG)
"""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# -----------------------------------------------------------------------
# Source: SQLite
# -----------------------------------------------------------------------
SQLITE_URL = f"sqlite:///{PROJECT_ROOT / 'healthmate.db'}"
sqlite_engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})

# -----------------------------------------------------------------------
# Target: Supabase PostgreSQL
# -----------------------------------------------------------------------
PG_URL = os.environ.get("DATABASE_URL", "")
if not PG_URL or "sqlite" in PG_URL:
    print("ERROR: DATABASE_URL in .env must point to PostgreSQL, not SQLite.")
    print("  Set: DATABASE_URL=postgresql://postgres.xxxx:password@aws-0-region.pooler.supabase.com:6543/postgres")
    sys.exit(1)

pg_engine = create_engine(PG_URL, pool_pre_ping=True)

# -----------------------------------------------------------------------
# Migration order (respects FK dependency chain)
# -----------------------------------------------------------------------
TABLE_ORDER = [
    "users",
    "documents",
    "prescriptions",
    "lab_tests",
    "vital_records",
    "rag_chunks",
    "medical_knowledge_chunks",
    "prescription_extractions",
    "extraction_corrections",
    "appointment_summaries",
    "nutrition_foods",
    "medication_reminders",
    "notifications",
    "shared_links",
    "audit_logs",
]


def get_table_columns(engine, table_name):
    insp = inspect(engine)
    if table_name not in insp.get_table_names():
        return []
    return [c["name"] for c in insp.get_columns(table_name)]


def get_pk_column(engine, table_name):
    insp = inspect(engine)
    pk_cols = insp.get_pk_constraint(table_name).get("constrained_columns", ["id"])
    return pk_cols[0] if pk_cols else "id"


def migrate_table(table_name: str) -> int:
    src_cols = get_table_columns(sqlite_engine, table_name)
    dst_cols = get_table_columns(pg_engine, table_name)

    if not src_cols:
        print(f"  [{table_name}] SKIP — not found in SQLite source")
        return 0
    if not dst_cols:
        print(f"  [{table_name}] SKIP — not found in PostgreSQL (run FastAPI startup first to create tables)")
        return 0

    # Only migrate columns present in both source and destination
    common_cols = [c for c in src_cols if c in dst_cols]
    col_list    = ", ".join(f'"{c}"' for c in common_cols)
    placeholders = ", ".join(f":{c}" for c in common_cols)
    pk_col = get_pk_column(sqlite_engine, table_name)

    insert_sql = text(f"""
        INSERT INTO "{table_name}" ({col_list})
        VALUES ({placeholders})
        ON CONFLICT ("{pk_col}") DO NOTHING
    """)

    with sqlite_engine.connect() as src_conn:
        rows = src_conn.execute(text(f'SELECT {col_list} FROM "{table_name}"')).mappings().all()

    if not rows:
        print(f"  [{table_name}] 0 rows in SQLite — nothing to migrate")
        return 0

    inserted = 0
    skipped = 0
    with pg_engine.begin() as dst_conn:
        for row in rows:
            row_dict = dict(row)
            # Convert SQLite BLOB bytes → string where needed
            for k, v in row_dict.items():
                if isinstance(v, bytes):
                    row_dict[k] = v.decode("utf-8", errors="replace")
            try:
                dst_conn.execute(insert_sql, row_dict)
                inserted += 1
            except Exception as e:
                skipped += 1
                if skipped <= 3:  # only show first 3 warnings per table
                    print(f"    WARNING: row id={row_dict.get('id','?')} skipped — {e}")

    status = f"{inserted}/{len(rows)} rows migrated"
    if skipped:
        status += f" ({skipped} skipped)"
    print(f"  [{table_name}] {status}")
    return inserted


def reset_sequences():
    """Reset PostgreSQL sequences after bulk insert to avoid PK conflicts on new inserts."""
    print("\n  Resetting PostgreSQL sequences...")
    with pg_engine.begin() as conn:
        for table in TABLE_ORDER:
            cols = get_table_columns(pg_engine, table)
            if "id" not in cols:
                continue
            try:
                conn.execute(text(f"""
                    SELECT setval(
                        pg_get_serial_sequence('"{table}"', 'id'),
                        COALESCE((SELECT MAX(id) FROM "{table}"), 1)
                    )
                """))
                print(f"    [{table}] sequence reset")
            except Exception as e:
                print(f"    [{table}] sequence reset skipped: {e}")


def main():
    print("=" * 62)
    print("  HealthMate AI — SQLite → Supabase PostgreSQL Migration")
    print("=" * 62)
    print(f"  Source : {SQLITE_URL}")
    print(f"  Target : {PG_URL[:65]}...")
    print()

    # Connectivity check
    try:
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("  PostgreSQL connection : OK")
    except Exception as e:
        print(f"  PostgreSQL connection FAILED: {e}")
        sys.exit(1)

    try:
        with sqlite_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("  SQLite connection     : OK")
    except Exception as e:
        print(f"  SQLite connection FAILED: {e}")
        sys.exit(1)

    print()
    print("  Migrating tables...")
    print()

    total_rows = 0
    for table in TABLE_ORDER:
        total_rows += migrate_table(table)

    reset_sequences()

    print()
    print("=" * 62)
    print(f"  Migration complete. Total rows inserted: {total_rows}")
    print()
    print("  Verification steps:")
    print("  1. Open Supabase Dashboard -> Table Editor")
    print("  2. Confirm row counts match your local SQLite data")
    print("  3. Keep DATABASE_URL pointing to PostgreSQL in .env")
    print("  4. DO NOT delete healthmate.db until fully verified")
    print("=" * 62)


if __name__ == "__main__":
    main()
