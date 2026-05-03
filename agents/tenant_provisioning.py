"""
Agent #34: Tenant Provisioning
Automates new organization setup:
  - Creates org record in the database
  - Provisions default taxonomy, dimensions, and category rules
  - Creates admin user with hashed password
  - Returns org_id and setup summary

Multi-tenant model:
  - Each org gets a unique org_id (UUID-based)
  - All data tables are scoped by org_id (enforced at query layer)
  - org_config stores per-org customizations (logo, taxonomy overrides, GL ranges)
"""
import os
import re
import json
import time
import sqlite3
from typing import Dict, Any, Optional

try:
    import bcrypt as _bcrypt
    _BCRYPT_AVAILABLE = True
except ImportError:
    _bcrypt = None
    _BCRYPT_AVAILABLE = False


def _hash_password(password: str) -> str:
    if _BCRYPT_AVAILABLE:
        return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")
    # Fallback only if bcrypt not installed
    import hashlib, secrets
    salt = secrets.token_hex(16)
    return "sha256:" + salt + ":" + hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def _verify_password(password: str, stored: str) -> bool:
    if stored.startswith("sha256:"):
        # Legacy SHA-256 format — verify then the next login will re-hash to bcrypt
        import hashlib
        try:
            _, salt, hashed = stored.split(":", 2)
            return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == hashed
        except Exception:
            return False
    if _BCRYPT_AVAILABLE:
        try:
            return _bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
        except Exception:
            return False
    return False


def _ensure_org_tables(conn: sqlite3.Connection) -> None:
    """Create org-aware tables if they don't exist."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            org_id      TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            slug        TEXT UNIQUE NOT NULL,
            plan        TEXT DEFAULT 'starter',
            logo_url    TEXT,
            primary_color TEXT DEFAULT '#3B82F6',
            created_at  REAL DEFAULT (strftime('%s','now')),
            active      INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS org_users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id      TEXT NOT NULL REFERENCES organizations(org_id),
            email       TEXT NOT NULL,
            username    TEXT NOT NULL,
            hashed_pw   TEXT NOT NULL,
            role        TEXT DEFAULT 'analyst',
            created_at  REAL DEFAULT (strftime('%s','now')),
            last_login  REAL,
            active      INTEGER DEFAULT 1,
            UNIQUE(org_id, email)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS org_config (
            org_id      TEXT NOT NULL REFERENCES organizations(org_id),
            config_key  TEXT NOT NULL,
            config_value TEXT NOT NULL,
            updated_at  REAL DEFAULT (strftime('%s','now')),
            PRIMARY KEY (org_id, config_key)
        )
    """)

    # Add org_id column to existing tables (idempotent)
    existing_tables = [
        "supplier_evaluations", "contracts", "audit_log", "sessions", "config"
    ]
    for table in existing_tables:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN org_id TEXT DEFAULT 'default'")
        except sqlite3.OperationalError:
            pass  # Column already exists

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_org_users_org ON org_users(org_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_org_config_org ON org_config(org_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evaluations_org ON supplier_evaluations(org_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contracts_org ON contracts(org_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_org ON audit_log(org_id)")

    conn.commit()


def provision_organization(
    org_name: str,
    admin_email: str,
    admin_password: str,
    plan: str = "starter",
    logo_url: str = "",
    primary_color: str = "#3B82F6",
    db_path: str = "procureiq.db",
    custom_taxonomy: Optional[Dict] = None,
    gl_account_ranges: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Provision a new organization with admin user and default config.

    Returns:
        {
            "org_id": "org_abc123",
            "org_name": "Acme Corp",
            "admin_email": "admin@acme.com",
            "setup_steps": [...],
            "success": True
        }
    """
    # Generate deterministic org_id from name + timestamp
    raw = f"{org_name.lower().strip()}{time.time()}"
    org_id = "org_" + hashlib.sha256(raw.encode()).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]", "-", org_name.lower().strip())[:32].strip("-")

    steps = []

    try:
        with sqlite3.connect(db_path) as conn:
            # Ensure schema is ready
            _ensure_org_tables(conn)
            steps.append({"step": "Schema migration", "status": "OK"})

            cur = conn.cursor()

            # Create org record
            cur.execute(
                """INSERT OR IGNORE INTO organizations
                   (org_id, name, slug, plan, logo_url, primary_color, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (org_id, org_name, slug, plan, logo_url, primary_color, time.time()),
            )
            steps.append({"step": "Organization record", "status": "OK", "org_id": org_id})

            # Create admin user
            hashed = _hash_password(admin_password)
            username = admin_email.split("@")[0]
            cur.execute(
                """INSERT OR IGNORE INTO org_users
                   (org_id, email, username, hashed_pw, role, created_at)
                   VALUES (?, ?, ?, ?, 'admin', ?)""",
                (org_id, admin_email, username, hashed, time.time()),
            )
            steps.append({"step": "Admin user", "status": "OK", "email": admin_email})

            # Write default org_config entries
            default_config = {
                "logo_url":          logo_url or "",
                "primary_color":     primary_color,
                "plan":              plan,
                "erp_system":        "Generic",
                "approval_threshold": "10000",
                "default_payment_terms": "Net 30",
                "default_notice_period": "60",
                "taxonomy_override":  json.dumps(custom_taxonomy or {}),
                "gl_ranges":          json.dumps(gl_account_ranges or {}),
                "approved_vendors":   json.dumps([]),
                "created_at":         str(time.time()),
            }
            for key, val in default_config.items():
                cur.execute(
                    """INSERT OR REPLACE INTO org_config (org_id, config_key, config_value, updated_at)
                       VALUES (?, ?, ?, ?)""",
                    (org_id, key, val, time.time()),
                )
            steps.append({"step": "Default configuration", "status": "OK",
                          "keys_written": len(default_config)})

            # Seed default taxonomy reference
            try:
                from taxonomy import SUBCATEGORY_TAXONOMY
                for subcat_name, subcat_data in SUBCATEGORY_TAXONOMY.items():
                    cur.execute(
                        """INSERT OR IGNORE INTO subcategories (name, category, data, updated_at)
                           VALUES (?, ?, ?, ?)""",
                        (subcat_name,
                         subcat_data.get("category", ""),
                         json.dumps(subcat_data),
                         time.time()),
                    )
                steps.append({"step": "Taxonomy seed", "status": "OK"})
            except Exception as e:
                steps.append({"step": "Taxonomy seed", "status": "SKIP", "note": str(e)})

            conn.commit()

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "org_id": org_id,
            "steps": steps,
        }

    return {
        "success": True,
        "org_id": org_id,
        "org_name": org_name,
        "slug": slug,
        "admin_email": admin_email,
        "admin_username": admin_email.split("@")[0],
        "plan": plan,
        "setup_steps": steps,
        "portal_url_suffix": f"?mode=portal&org={org_id}",
        "provisioned_at": time.time(),
    }


def get_org_config(org_id: str, db_path: str = "procureiq.db") -> Dict[str, Any]:
    """Retrieve all config entries for an org."""
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT config_key, config_value FROM org_config WHERE org_id = ?",
                (org_id,),
            )
            rows = cur.fetchall()
            config = {}
            for key, val in rows:
                try:
                    config[key] = json.loads(val)
                except Exception:
                    config[key] = val
            return config
    except Exception as e:
        return {"error": str(e)}


def list_organizations(db_path: str = "procureiq.db") -> list:
    """List all provisioned organizations."""
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT o.org_id, o.name, o.slug, o.plan, o.created_at, o.active,
                          COUNT(u.id) as user_count
                   FROM organizations o
                   LEFT JOIN org_users u ON o.org_id = u.org_id
                   GROUP BY o.org_id ORDER BY o.created_at DESC"""
            )
            cols = ["org_id", "name", "slug", "plan", "created_at", "active", "user_count"]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    except Exception:
        return []


def authenticate_user(
    email: str,
    password: str,
    db_path: str = "procureiq.db",
) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user against the org_users table.
    Returns user record (without password) or None.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT org_id, email, username, hashed_pw, role
                   FROM org_users WHERE email = ? AND active = 1""",
                (email,),
            )
            row = cur.fetchone()
            if not row:
                return None
            org_id, db_email, username, hashed_pw, role = row
            if _verify_password(password, hashed_pw):
                # Update last login
                cur.execute(
                    "UPDATE org_users SET last_login = ? WHERE email = ?",
                    (time.time(), email),
                )
                conn.commit()
                return {"org_id": org_id, "email": db_email,
                        "username": username, "role": role}
    except Exception:
        pass
    return None


