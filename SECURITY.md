# ProcureIQ — Security

This document describes the security controls that are present, their scope, and their limitations.
It is written for portfolio transparency, not as a compliance attestation.

---

## What Is Implemented

### Authentication (Streamlit login gate)
- Custom `auth.py` login form blocks all app access before the first Streamlit widget renders.
  Uses `bcrypt.checkpw()` directly — no third-party auth library.
- Credentials loaded from `auth_config.yaml` (gitignored) or env vars `PROCUREIQ_DEMO_USER` / `PROCUREIQ_DEMO_PASS`.
- Passwords stored as bcrypt hashes — never plaintext in code or session state.
- Session stored in `st.session_state`. **Not cookie-based.** Session ends on browser refresh or server restart.
- **Scope:** demo-grade only. No MFA, SSO, role-based access control, brute-force lockout, or persistent sessions on the Streamlit layer.

### Authentication (FastAPI layer)
- JWT tokens signed with HS256 (`python-jose`).
- Passwords hashed with bcrypt via `passlib` (`verify_password` / `hash_password` in `security.py`).
- `SECRET_KEY` must be set as an environment variable before JWT endpoints are active.
  The app refuses to issue tokens if `SECRET_KEY` is absent or shorter than 32 characters.
- Session records stored in SQLite with expiry.

### Rate Limiting on `/login`
- In-memory per-IP counter: 5 failed attempts within a 5-minute window triggers HTTP 429.
- Counter resets automatically after the window expires.
- **Limitation:** counter is process-local and resets on server restart. Distributed deployments
  would need a shared store (Redis, Memcached).

### Audit Logging
- `db.log_audit_event()` writes to the SQLite `audit_log` table on every login, failed login,
  logout, RFP validation, and protected-endpoint access.
- `AuditLogger` (security.py) optionally writes an encrypted copy to `audit_log.enc`
  when the `cryptography` package is installed.
- **Limitation:** The SQLite audit log is not tamper-evident. `audit_log.enc` is encrypted with
  a Fernet key that is regenerated on each server restart unless `PROCUREIQ_ENCRYPTION_KEY` is
  set — events written in a prior session cannot be decrypted after restart without that variable.

### Encryption (optional)
- `SecurityManager` uses `cryptography.fernet.Fernet` (AES-128-CBC + HMAC-SHA256) for field
  encryption and audit log encryption.
- Requires `cryptography` package. Falls back gracefully if not installed.

### Password Safety
- `bcrypt` library used directly for all password hashing in `auth.py` (`bcrypt.checkpw()`).
- Passwords in `auth_config.yaml` are stored as bcrypt hashes only — never plaintext.
- The app never silently accepts a plaintext password comparison.

---

## What Is NOT Implemented

| Control | Status |
|---------|--------|
| Streamlit UI authentication | **Demo-grade** — custom `auth.py` login gate using `bcrypt.checkpw`; credentials in `auth_config.yaml` (gitignored); session via `st.session_state` only |
| Multi-tenancy / user isolation | **Not present** — all data in a single instance is shared |
| SQLite encryption at rest | **Not present** — database file is unencrypted |
| Rate limiting on Streamlit layer | **Not present** |
| HTTPS / TLS termination | **Not provided** — run behind a reverse proxy (nginx, Caddy) for TLS |
| TOTP / MFA | Stub class exists in `security.py`; not wired to any login flow |
| SOX / GDPR / ISO 27001 audit trail | The audit log is informational only; not a certified audit trail |
| OFAC / SAM.gov sanctions screening | Stub only — not a replacement for certified compliance tooling |
| CSP / security headers | Not configured on the Streamlit layer |
| Secrets scanning | No pre-commit hook; never commit `.env` or credentials to version control |

---

## Configuration

```bash
# ── Streamlit login gate (required) ─────────────────────────────────────────

# Option A: config file (recommended)
cp auth_config.yaml.example auth_config.yaml
# Edit auth_config.yaml — set bcrypt-hashed passwords, then restart.

# Option B: environment variables
export PROCUREIQ_DEMO_USER=demo
export PROCUREIQ_DEMO_PASS=$(python3 -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())")

# ── FastAPI JWT layer (required only if using API endpoints) ─────────────────

# Required for JWT to function — minimum 32 characters
export SECRET_KEY="change-this-to-a-random-string-of-at-least-32-chars"

# Optional: hash admin password with bcrypt before setting
export API_ADMIN_PASSWORD_HASH="<bcrypt-hash>"

# Optional: stable Fernet key so audit_log.enc survives restarts
export PROCUREIQ_ENCRYPTION_KEY="<44-char-base64-Fernet-key>"
```

Generate a Fernet key:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

---

## Suitable Use

ProcureIQ is suitable for:
- Personal use on a local machine or private network.
- Portfolio demonstrations where no real supplier PII or commercial secrets are stored.
- Development and experimentation.

ProcureIQ is **not suitable** for:
- Processing real PII or commercially sensitive data without significant additional hardening.
- Multi-user production deployment without authentication on the Streamlit layer.
- Any context where the controls above create legal, compliance, or business risk.

See [LIMITATIONS.md](LIMITATIONS.md) for the full limitations list.
