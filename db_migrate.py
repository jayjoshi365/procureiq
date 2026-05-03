"""
ProcureIQ Database Migration Script
Migrates from SQLite to PostgreSQL and applies schema upgrades.

Usage:
    # Migrate SQLite → PostgreSQL
    DATABASE_URL=postgresql://user:pass@host/procureiq python db_migrate.py

    # Apply org_id schema only (SQLite)
    python db_migrate.py --sqlite-only

    # Check current schema
    python db_migrate.py --status
"""
import argparse
import json
import os
import sqlite3
import sys
import time

_DATABASE_URL = os.getenv("DATABASE_URL", "")
_SQLITE_PATH  = os.getenv("SQLITE_PATH", "procureiq.db")


# ── PostgreSQL schema DDL ─────────────────────────────────────────────

PG_SCHEMA = """
-- Core config
CREATE TABLE IF NOT EXISTS config (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW())
);

-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id    TEXT,
    org_id     TEXT DEFAULT 'default',
    data       TEXT NOT NULL,
    created_at DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW()),
    expires_at DOUBLE PRECISION
);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_org ON sessions(org_id);

-- Audit log
CREATE TABLE IF NOT EXISTS audit_log (
    id         SERIAL PRIMARY KEY,
    org_id     TEXT DEFAULT 'default',
    user_id    TEXT,
    action     TEXT NOT NULL,
    resource   TEXT,
    details    TEXT,
    ip_address TEXT,
    timestamp  DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW())
);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_org ON audit_log(org_id);

-- Market data cache
CREATE TABLE IF NOT EXISTS market_data_cache (
    ticker     TEXT PRIMARY KEY,
    data       TEXT NOT NULL,
    fetched_at DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW()),
    expires_at DOUBLE PRECISION
);
CREATE INDEX IF NOT EXISTS idx_market_expires ON market_data_cache(expires_at);

-- Supplier evaluations
CREATE TABLE IF NOT EXISTS supplier_evaluations (
    id              SERIAL PRIMARY KEY,
    org_id          TEXT DEFAULT 'default',
    event_id        TEXT NOT NULL,
    supplier_data   TEXT NOT NULL,
    scores          TEXT,
    recommendation  TEXT,
    created_at      DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW())
);
CREATE INDEX IF NOT EXISTS idx_eval_event ON supplier_evaluations(event_id);
CREATE INDEX IF NOT EXISTS idx_eval_org ON supplier_evaluations(org_id);

-- Subcategories
CREATE TABLE IF NOT EXISTS subcategories (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    category   TEXT NOT NULL,
    data       TEXT NOT NULL,
    updated_at DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW())
);

-- Market leaders
CREATE TABLE IF NOT EXISTS market_leaders (
    id           SERIAL PRIMARY KEY,
    subcategory  TEXT NOT NULL,
    name         TEXT NOT NULL,
    market_share TEXT,
    strength     TEXT,
    watch        TEXT,
    ticker       TEXT,
    updated_at   DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW()),
    UNIQUE(subcategory, name)
);

-- Contracts
CREATE TABLE IF NOT EXISTS contracts (
    id             SERIAL PRIMARY KEY,
    org_id         TEXT DEFAULT 'default',
    event_id       TEXT NOT NULL,
    supplier_name  TEXT NOT NULL,
    category       TEXT,
    subcategory    TEXT,
    award_date     DOUBLE PRECISION,
    expiry_date    DOUBLE PRECISION,
    annual_value   DOUBLE PRECISION,
    sla_target     TEXT,
    status         TEXT DEFAULT 'Active',
    health_score   INTEGER DEFAULT 75,
    notes          TEXT,
    created_at     DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW()),
    updated_at     DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW())
);
CREATE INDEX IF NOT EXISTS idx_contracts_supplier ON contracts(supplier_name);
CREATE INDEX IF NOT EXISTS idx_contracts_expiry ON contracts(expiry_date);
CREATE INDEX IF NOT EXISTS idx_contracts_org ON contracts(org_id);

-- Organizations
CREATE TABLE IF NOT EXISTS organizations (
    org_id        TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    slug          TEXT UNIQUE NOT NULL,
    plan          TEXT DEFAULT 'starter',
    logo_url      TEXT,
    primary_color TEXT DEFAULT '#3B82F6',
    created_at    DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW()),
    active        INTEGER DEFAULT 1
);

-- Org users
CREATE TABLE IF NOT EXISTS org_users (
    id         SERIAL PRIMARY KEY,
    org_id     TEXT NOT NULL REFERENCES organizations(org_id),
    email      TEXT NOT NULL,
    username   TEXT NOT NULL,
    hashed_pw  TEXT NOT NULL,
    role       TEXT DEFAULT 'analyst',
    created_at DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW()),
    last_login DOUBLE PRECISION,
    active     INTEGER DEFAULT 1,
    UNIQUE(org_id, email)
);
CREATE INDEX IF NOT EXISTS idx_org_users ON org_users(org_id);

-- Org config
CREATE TABLE IF NOT EXISTS org_config (
    org_id       TEXT NOT NULL REFERENCES organizations(org_id),
    config_key   TEXT NOT NULL,
    config_value TEXT NOT NULL,
    updated_at   DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW()),
    PRIMARY KEY (org_id, config_key)
);
CREATE INDEX IF NOT EXISTS idx_org_config ON org_config(org_id);
"""

# SQLite org_id upgrade (additive only)
SQLITE_UPGRADE = """
ALTER TABLE supplier_evaluations ADD COLUMN org_id TEXT DEFAULT 'default';
ALTER TABLE contracts            ADD COLUMN org_id TEXT DEFAULT 'default';
ALTER TABLE audit_log            ADD COLUMN org_id TEXT DEFAULT 'default';
ALTER TABLE sessions             ADD COLUMN org_id TEXT DEFAULT 'default';
CREATE TABLE IF NOT EXISTS organizations (
    org_id TEXT PRIMARY KEY, name TEXT NOT NULL, slug TEXT UNIQUE NOT NULL,
    plan TEXT DEFAULT 'starter', logo_url TEXT, primary_color TEXT DEFAULT '#3B82F6',
    created_at REAL DEFAULT (strftime('%s','now')), active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS org_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, org_id TEXT NOT NULL, email TEXT NOT NULL,
    username TEXT NOT NULL, hashed_pw TEXT NOT NULL, role TEXT DEFAULT 'analyst',
    created_at REAL DEFAULT (strftime('%s','now')), last_login REAL, active INTEGER DEFAULT 1,
    UNIQUE(org_id, email)
);
CREATE TABLE IF NOT EXISTS org_config (
    org_id TEXT NOT NULL, config_key TEXT NOT NULL, config_value TEXT NOT NULL,
    updated_at REAL DEFAULT (strftime('%s','now')), PRIMARY KEY (org_id, config_key)
);
"""


def apply_sqlite_upgrade(db_path: str) -> None:
    """Add org_id columns and org tables to existing SQLite DB."""
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        for stmt in SQLITE_UPGRADE.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    cur.execute(stmt)
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                        pass  # Idempotent
                    else:
                        print(f"  WARN: {e}")
        conn.commit()
    print(f"✅ SQLite schema upgraded: {db_path}")


def create_pg_schema(pg_url: str) -> None:
    """Create full PostgreSQL schema."""
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)

    conn = psycopg2.connect(pg_url)
    conn.autocommit = True
    cur = conn.cursor()
    for stmt in PG_SCHEMA.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            try:
                cur.execute(stmt)
            except Exception as e:
                print(f"  WARN: {e}")
    conn.close()
    print("✅ PostgreSQL schema created.")


def migrate_sqlite_to_pg(sqlite_path: str, pg_url: str) -> None:
    """Copy all data from SQLite to PostgreSQL."""
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        print("❌ psycopg2 not installed.")
        sys.exit(1)

    print(f"Migrating {sqlite_path} → PostgreSQL ...")
    create_pg_schema(pg_url)

    sq_conn = sqlite3.connect(sqlite_path)
    sq_conn.row_factory = sqlite3.Row
    pg_conn = psycopg2.connect(pg_url)

    TABLES = [
        "config", "sessions", "audit_log", "market_data_cache",
        "supplier_evaluations", "subcategories", "market_leaders", "contracts",
    ]

    for table in TABLES:
        sq_cur = sq_conn.cursor()
        try:
            sq_cur.execute(f"SELECT * FROM {table}")
            rows = sq_cur.fetchall()
        except Exception:
            print(f"  SKIP {table} (not found in SQLite)")
            continue

        if not rows:
            print(f"  SKIP {table} (empty)")
            continue

        cols = [d[0] for d in sq_cur.description]
        pg_cur = pg_conn.cursor()

        col_str = ", ".join(cols)
        placeholder = ", ".join(["%s"] * len(cols))
        insert_sql = (
            f"INSERT INTO {table} ({col_str}) VALUES ({placeholder}) "
            f"ON CONFLICT DO NOTHING"
        )

        batch = [tuple(row) for row in rows]
        psycopg2.extras.execute_batch(pg_cur, insert_sql, batch, page_size=500)
        pg_conn.commit()
        print(f"  ✓ {table}: {len(batch)} rows migrated")

    sq_conn.close()
    pg_conn.close()
    print("✅ Migration complete.")


def status(sqlite_path: str) -> None:
    """Print current schema status."""
    with sqlite3.connect(sqlite_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]
        print(f"\nSQLite: {sqlite_path}")
        print(f"Tables: {', '.join(tables)}")
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            count = cur.fetchone()[0]
            cur.execute(f"PRAGMA table_info({t})")
            cols = [c[1] for c in cur.fetchall()]
            org_aware = "org_id" in cols
            print(f"  {t:35s}  rows={count:6d}  org_aware={'✓' if org_aware else '✗'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ProcureIQ DB Migration")
    parser.add_argument("--sqlite-only", action="store_true",
                        help="Apply org_id upgrade to SQLite only")
    parser.add_argument("--status", action="store_true",
                        help="Show current schema status")
    parser.add_argument("--sqlite-path", default=_SQLITE_PATH)
    args = parser.parse_args()

    if args.status:
        status(args.sqlite_path)
    elif args.sqlite_only:
        apply_sqlite_upgrade(args.sqlite_path)
    elif _DATABASE_URL:
        migrate_sqlite_to_pg(args.sqlite_path, _DATABASE_URL)
    else:
        print("No DATABASE_URL set. Running SQLite upgrade only.")
        apply_sqlite_upgrade(args.sqlite_path)
