"""Database integration for ProcureIQ
Supports both SQLite (development) and PostgreSQL (production).
Set DATABASE_URL=postgresql://user:pass@host/dbname to switch to PostgreSQL.
"""
import sqlite3
import json
import os
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from threading import Lock
import hashlib

# ── PostgreSQL support (optional) ────────────────────────────────────
_DATABASE_URL = os.getenv("DATABASE_URL", "")
_USE_PG = bool(_DATABASE_URL and _DATABASE_URL.startswith("postgres"))

if _USE_PG:
    try:
        import psycopg2
        import psycopg2.extras
        _PG_AVAILABLE = True
    except ImportError:
        _PG_AVAILABLE = False
        _USE_PG = False
else:
    _PG_AVAILABLE = False


def _get_pg_conn():
    """Get a PostgreSQL connection from DATABASE_URL."""
    return psycopg2.connect(_DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def _sqlite_to_pg_sql(sql: str) -> str:
    """Minimal SQLite→PostgreSQL SQL translation."""
    sql = sql.replace("?", "%s")
    sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    sql = sql.replace("strftime('%s', 'now')", "EXTRACT(EPOCH FROM NOW())")
    sql = sql.replace("strftime('%s','now')", "EXTRACT(EPOCH FROM NOW())")
    sql = sql.replace("INSERT OR REPLACE", "INSERT")
    sql = sql.replace("INSERT OR IGNORE", "INSERT")
    return sql


class _DBConn:
    """Context manager that returns the right DB connection (SQLite or PG)."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None

    def __enter__(self):
        if _USE_PG and _PG_AVAILABLE:
            self._conn = _get_pg_conn()
        else:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL;")
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            if exc_type:
                self._conn.rollback()
            else:
                self._conn.commit()
            self._conn.close()
        return False


class Cache:
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        self._cache = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry is None or time.time() < expiry:
                    return value
                else:
                    del self._cache[key]
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Set cached value with optional TTL."""
        with self._lock:
            expiry = time.time() + ttl_seconds if ttl_seconds else None
            self._cache[key] = (value, expiry)

    def delete(self, key: str):
        """Delete cached value."""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self):
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()


class ProcureIQDatabase:
    """Database wrapper for ProcureIQ — SQLite (dev) or PostgreSQL (prod)."""

    def __init__(self, db_path: str = "procureiq.db"):
        self.db_path = db_path
        self.use_pg = _USE_PG and _PG_AVAILABLE
        self.cache = Cache()
        self.cache_ttl = 300
        self._init_db()

    def _conn(self) -> _DBConn:
        return _DBConn(self.db_path)

    def _init_db(self):
        """Initialize all tables including org-aware schema."""
        with self._conn() as conn:
            cursor = conn.cursor()

            # Enhanced tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at REAL DEFAULT (strftime('%s', 'now'))
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    data TEXT NOT NULL,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    expires_at REAL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    resource TEXT,
                    details TEXT,
                    timestamp REAL DEFAULT (strftime('%s', 'now'))
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_data_cache (
                    ticker TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    fetched_at REAL DEFAULT (strftime('%s', 'now')),
                    expires_at REAL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS supplier_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    supplier_data TEXT NOT NULL,
                    scores TEXT,
                    recommendation TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subcategories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    data TEXT NOT NULL,
                    updated_at REAL DEFAULT (strftime('%s', 'now'))
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_leaders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subcategory TEXT NOT NULL,
                    name TEXT NOT NULL,
                    market_share TEXT,
                    strength TEXT,
                    watch TEXT,
                    ticker TEXT,
                    updated_at REAL DEFAULT (strftime('%s', 'now')),
                    UNIQUE(subcategory, name)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contracts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    supplier_name TEXT NOT NULL,
                    category TEXT,
                    subcategory TEXT,
                    award_date REAL,
                    expiry_date REAL,
                    annual_value REAL,
                    sla_target TEXT,
                    status TEXT DEFAULT 'Active',
                    health_score INTEGER DEFAULT 75,
                    notes TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    updated_at REAL DEFAULT (strftime('%s', 'now'))
                )
            ''')

            # Org-aware tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS organizations (
                    org_id       TEXT PRIMARY KEY,
                    name         TEXT NOT NULL,
                    slug         TEXT UNIQUE NOT NULL,
                    plan         TEXT DEFAULT 'starter',
                    logo_url     TEXT,
                    primary_color TEXT DEFAULT '#3B82F6',
                    created_at   REAL DEFAULT (strftime('%s','now')),
                    active       INTEGER DEFAULT 1
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS org_users (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id     TEXT NOT NULL,
                    email      TEXT NOT NULL,
                    username   TEXT NOT NULL,
                    hashed_pw  TEXT NOT NULL,
                    role       TEXT DEFAULT 'analyst',
                    created_at REAL DEFAULT (strftime('%s','now')),
                    last_login REAL,
                    active     INTEGER DEFAULT 1,
                    UNIQUE(org_id, email)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS org_config (
                    org_id       TEXT NOT NULL,
                    config_key   TEXT NOT NULL,
                    config_value TEXT NOT NULL,
                    updated_at   REAL DEFAULT (strftime('%s','now')),
                    PRIMARY KEY (org_id, config_key)
                )
            ''')

            # Add org_id to existing tables (idempotent — fails silently if column exists)
            for _table in ("supplier_evaluations", "contracts", "audit_log", "sessions"):
                try:
                    cursor.execute(f"ALTER TABLE {_table} ADD COLUMN org_id TEXT DEFAULT 'default'")
                except Exception:
                    pass

            # Indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_data_expires ON market_data_cache(expires_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_evaluations_event ON supplier_evaluations(event_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_contracts_supplier ON contracts(supplier_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_contracts_expiry ON contracts(expiry_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_org_users ON org_users(org_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_org_config ON org_config(org_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_evaluations_org ON supplier_evaluations(org_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_contracts_org ON contracts(org_id)')

            conn.commit()

    def _get_cache_key(self, operation: str, *args) -> str:
        """Generate cache key for operations."""
        key_parts = [operation] + [str(arg) for arg in args]
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()

    # Session management
    def create_session(self, user_id: str, data: Dict, ttl_seconds: int = 3600) -> str:
        """Create a new session."""
        session_id = hashlib.sha256(f"{user_id}{time.time()}".encode()).hexdigest()[:32]
        expires_at = time.time() + ttl_seconds

        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO sessions (session_id, user_id, data, expires_at) VALUES (?, ?, ?, ?)',
                (session_id, user_id, json.dumps(data), expires_at)
            )
            conn.commit()

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data."""
        cache_key = self._get_cache_key("session", session_id)
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT user_id, data, expires_at FROM sessions WHERE session_id = ? AND expires_at > ?',
                (session_id, time.time())
            )
            result = cursor.fetchone()

            if result:
                user_id, data, expires_at = result
                session_data = {
                    "user_id": user_id,
                    "data": json.loads(data),
                    "expires_at": expires_at
                }
                self.cache.set(cache_key, session_data, ttl_seconds=300)
                return session_data

        return None

    def update_session(self, session_id: str, data: Dict):
        """Update session data."""
        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE sessions SET data = ? WHERE session_id = ?',
                (json.dumps(data), session_id)
            )
            conn.commit()

        # Clear cache
        cache_key = self._get_cache_key("session", session_id)
        self.cache.delete(cache_key)

    def delete_session(self, session_id: str):
        """Delete session."""
        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            conn.commit()

        # Clear cache
        cache_key = self._get_cache_key("session", session_id)
        self.cache.delete(cache_key)

    # Audit logging
    def log_audit_event(self, user_id: str, action: str, resource: str = None, details: Dict = None):
        """Log audit event."""
        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO audit_log (user_id, action, resource, details) VALUES (?, ?, ?, ?)',
                (user_id, action, resource, json.dumps(details) if details else None)
            )
            conn.commit()

    def get_audit_log(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        """Get audit log entries."""
        with self._conn() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute(
                    'SELECT user_id, action, resource, details, timestamp FROM audit_log WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?',
                    (user_id, limit)
                )
            else:
                cursor.execute(
                    'SELECT user_id, action, resource, details, timestamp FROM audit_log ORDER BY timestamp DESC LIMIT ?',
                    (limit,)
                )

            return [{
                "user_id": row[0],
                "action": row[1],
                "resource": row[2],
                "details": json.loads(row[3]) if row[3] else None,
                "timestamp": row[4]
            } for row in cursor.fetchall()]

    # Market data caching
    def cache_market_data(self, ticker: str, data: Dict, ttl_seconds: int = 900):  # 15 minutes
        """Cache market data."""
        expires_at = time.time() + ttl_seconds

        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO market_data_cache (ticker, data, expires_at) VALUES (?, ?, ?)',
                (ticker.upper(), json.dumps(data), expires_at)
            )
            conn.commit()

    def get_cached_market_data(self, ticker: str) -> Optional[Dict]:
        """Get cached market data if not expired."""
        cache_key = self._get_cache_key("market_data", ticker)
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT data, expires_at FROM market_data_cache WHERE ticker = ? AND expires_at > ?',
                (ticker.upper(), time.time())
            )
            result = cursor.fetchone()

            if result:
                data, expires_at = result
                market_data = json.loads(data)
                # Cache in memory for faster access
                ttl = int(expires_at - time.time())
                self.cache.set(cache_key, market_data, ttl_seconds=max(ttl, 60))
                return market_data

        return None

    # Supplier evaluations
    def save_evaluation(self, event_id: str, supplier_data: List[Dict], scores: Dict, recommendation: str):
        """Save supplier evaluation results."""
        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO supplier_evaluations (event_id, supplier_data, scores, recommendation) VALUES (?, ?, ?, ?)',
                (event_id, json.dumps(supplier_data), json.dumps(scores), recommendation)
            )
            conn.commit()

    def get_evaluation(self, event_id: str) -> Optional[Dict]:
        """Get evaluation by event ID."""
        cache_key = self._get_cache_key("evaluation", event_id)
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT supplier_data, scores, recommendation, created_at FROM supplier_evaluations WHERE event_id = ?',
                (event_id,)
            )
            result = cursor.fetchone()

            if result:
                supplier_data, scores, recommendation, created_at = result
                evaluation = {
                    "event_id": event_id,
                    "supplier_data": json.loads(supplier_data),
                    "scores": json.loads(scores),
                    "recommendation": recommendation,
                    "created_at": created_at
                }
                self.cache.set(cache_key, evaluation, ttl_seconds=3600)  # Cache for 1 hour
                return evaluation

        return None

    def get_evaluation_history(self, limit: int = 50) -> List[Dict]:
        """Get recent evaluation history."""
        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT event_id, supplier_data, scores, recommendation, created_at FROM supplier_evaluations ORDER BY created_at DESC LIMIT ?',
                (limit,)
            )

            return [{
                "event_id": row[0],
                "supplier_data": json.loads(row[1]),
                "scores": json.loads(row[2]),
                "recommendation": row[3],
                "created_at": row[4]
            } for row in cursor.fetchall()]

    # Legacy methods for backward compatibility
    def store_config(self, key: str, value):
        """Store configuration data."""
        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO config (key, value, updated_at) VALUES (?, ?, ?)',
                (key, json.dumps(value), time.time())
            )
            conn.commit()

    def get_config(self, key: str, default=None):
        """Retrieve configuration data."""
        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
            result = cursor.fetchone()
            return json.loads(result[0]) if result else default

    def store_subcategory(self, name: str, data: Dict):
        """Store subcategory data."""
        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO subcategories (name, data) VALUES (?, ?)',
                (name, json.dumps(data))
            )
            conn.commit()

    def get_subcategory(self, name: str) -> Optional[Dict]:
        """Retrieve subcategory data."""
        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT data FROM subcategories WHERE name = ?', (name,))
            result = cursor.fetchone()
            return json.loads(result[0]) if result else None

    def get_all_subcategories(self) -> Dict[str, Dict]:
        """Get all subcategories."""
        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name, data FROM subcategories')
            return {name: json.loads(data) for name, data in cursor.fetchall()}

    def store_market_leader(self, subcategory: str, name: str, data: Dict):
        """Store market leader data."""
        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO market_leaders (subcategory, name, data) VALUES (?, ?, ?)',
                (subcategory, name, json.dumps(data))
            )
            conn.commit()

    def get_market_leaders(self, subcategory: str) -> List[Dict]:
        """Get market leaders for a subcategory."""
        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT name, data FROM market_leaders WHERE subcategory = ?',
                (subcategory,)
            )
            return [{"name": name, **json.loads(data)} for name, data in cursor.fetchall()]

    def save_discovery_cache(self, cache_key: str, data: Dict, ttl_seconds: int = 86400):
        """Persist a discovery result keyed by a hash of the search parameters.
        Default TTL is 24 hours — live data changes slowly enough that re-running
        the same search the same day is wasteful.
        """
        expires_at = time.time() + ttl_seconds
        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO config (key, value, updated_at) VALUES (?, ?, ?)",
                (f"discovery_cache_{cache_key}", json.dumps({
                    "data": data, "expires_at": expires_at, "cached_at": time.time(),
                }), time.time()),
            )
            conn.commit()

    def get_discovery_cache(self, cache_key: str) -> Optional[Dict]:
        """Return a cached discovery result if it exists and has not expired.
        Returns None on cache miss or expiry.
        """
        row = self.get_config(f"discovery_cache_{cache_key}")
        if not row:
            return None
        if time.time() > row.get("expires_at", 0):
            return None
        return row.get("data")

    def get_config_by_prefix(self, prefix: str, limit: int = 30) -> List[Dict]:
        """Return config rows whose key starts with *prefix*, newest first.
        Each dict has ``key`` and ``value`` (already JSON-decoded).
        """
        with self._conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT key, value FROM config WHERE key LIKE ? ORDER BY updated_at DESC LIMIT ?",
                (f"{prefix}%", limit),
            )
            rows = []
            for key, raw in cursor.fetchall():
                try:
                    rows.append({"key": key, "value": json.loads(raw)})
                except Exception:
                    pass
            return rows

    def get_portfolio_events(self, limit: int = 8) -> List[Dict]:
        """Return recent portfolio events (config keys prefixed 'portfolio_')."""
        return self.get_config_by_prefix("portfolio_", limit=limit)

    def get_session_snapshots(self, limit: int = 6) -> List[Dict]:
        """Return recent session snapshots (config keys prefixed 'session_snap_')."""
        return self.get_config_by_prefix("session_snap_", limit=limit)

    def get_portal_submissions(self, event_ref: str = "", limit: int = 30) -> List[Dict]:
        """Return portal submissions, optionally filtered to a specific event_ref."""
        prefix = f"portal_submission_{event_ref}_" if event_ref else "portal_submission_"
        return self.get_config_by_prefix(prefix, limit=limit)

    def save_portal_submission(self, event_ref: str, submission_id: str, data: Dict):
        """Persist a single supplier portal submission."""
        key = f"portal_submission_{event_ref}_{submission_id}"
        self.store_config(key, data)

    def initialize_from_files(self):
        """Initialize database from existing Python files."""
        try:
            # Import data from modules
            from config import (
                DIMENSIONS, KRALJIC_INFO, AUCTION_TYPES, DEFAULT_RFP_QUESTIONS,
                USE_CASE_TEMPLATES, CATEGORY_RULES, FINANCIAL_FIELDS
            )
            from taxonomy import SUBCATEGORY_TAXONOMY
            from market_data import MARKET_LEADERS

            # Store config data
            self.store_config('dimensions', DIMENSIONS)
            self.store_config('kraljic_info', KRALJIC_INFO)
            self.store_config('auction_types', AUCTION_TYPES)
            self.store_config('default_rfp_questions', DEFAULT_RFP_QUESTIONS)
            self.store_config('use_case_templates', USE_CASE_TEMPLATES)
            self.store_config('category_rules', CATEGORY_RULES)
            self.store_config('financial_fields', FINANCIAL_FIELDS)

            # Store subcategories
            for name, data in SUBCATEGORY_TAXONOMY.items():
                self.store_subcategory(name, data)

            # Store market leaders
            for subcategory, leaders in MARKET_LEADERS.items():
                for leader in leaders:
                    name = leader.pop('name')  # Remove name from data dict
                    self.store_market_leader(subcategory, name, leader)

            print("Database initialized successfully!")

        except ImportError as e:
            print(f"Could not initialize database from files: {e}")


# Global database instance
_db = None

def get_database() -> ProcureIQDatabase:
    """Get database instance (singleton pattern)."""
    global _db
    if _db is None:
        _db = ProcureIQDatabase()
    return _db


def init_database():
    """Initialize database with data from files."""
    db = get_database()
    db.initialize_from_files()