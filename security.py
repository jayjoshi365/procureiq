"""
Enhanced security module for ProcureIQ
Provides MFA preparation, encryption, and advanced security features
"""

import os
import secrets
import hashlib
import hmac
import base64
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import json

# Conditional imports for optional dependencies
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import pyotp  # For TOTP MFA
    _CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    Fernet = None
    hashes = None
    PBKDF2HMAC = None
    pyotp = None
    _CRYPTOGRAPHY_AVAILABLE = False

class SecurityManager:
    """Enhanced security manager with encryption and MFA support."""

    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize security manager with encryption key."""
        if not _CRYPTOGRAPHY_AVAILABLE:
            raise ImportError("Cryptography library not available. Install cryptography to use advanced security features.")
        
        if encryption_key:
            self.encryption_key = encryption_key.encode()
        else:
            # Generate a key for development - in production, use environment variable
            self.encryption_key = os.getenv("PROCUREIQ_ENCRYPTION_KEY", "").encode()
            if not self.encryption_key:
                # Generate a random key for demo purposes
                self.encryption_key = Fernet.generate_key()

        self.fernet = Fernet(self.encryption_key)

    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception:
            raise ValueError("Failed to decrypt data")

    def hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash password with salt using PBKDF2."""
        if not salt:
            salt = secrets.token_hex(16)

        # Use PBKDF2 for password hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode(), salt

    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against hash."""
        expected_key, _ = self.hash_password(password, salt)
        return hmac.compare_digest(expected_key, hashed_password)

    def generate_api_key(self, user_id: str, scopes: list = None) -> str:
        """Generate a secure API key for a user."""
        if scopes is None:
            scopes = ["read"]

        # Create API key payload
        payload = {
            "user_id": user_id,
            "scopes": scopes,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=365)).isoformat()
        }

        # Encrypt the payload
        encrypted_payload = self.encrypt_data(json.dumps(payload))

        # Create API key with prefix
        api_key = f"pq_{secrets.token_urlsafe(32)}"

        return api_key

    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate API key and return user information.

        NOT IMPLEMENTED — requires a database lookup against a stored,
        hashed key table before this class can be used in a deployed
        FastAPI endpoint. Do not enable the FastAPI auth layer until
        this method performs a real lookup.
        """
        if not api_key.startswith("pq_"):
            return None
        raise NotImplementedError(
            "validate_api_key requires a database lookup. "
            "Implement key storage and hashed comparison before deploying."
        )

class MFAManager:
    """Multi-Factor Authentication manager using TOTP."""

    def __init__(self):
        if not _CRYPTOGRAPHY_AVAILABLE:
            raise ImportError("PyOTP library not available. Install pyotp to use MFA features.")
        self.secret_length = 32

    def generate_secret(self, user_id: str) -> str:
        """Generate TOTP secret for a user."""
        # In production, store this securely in database
        secret = pyotp.random_base32(length=self.secret_length)
        return secret

    def get_totp_uri(self, secret: str, user_id: str, issuer: str = "ProcureIQ") -> str:
        """Get TOTP URI for QR code generation."""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=user_id, issuer_name=issuer)

    def verify_totp(self, secret: str, code: str) -> bool:
        """Verify TOTP code."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code)

    def generate_backup_codes(self, user_id: str, count: int = 10) -> list:
        """Generate backup codes for account recovery."""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()  # 8-character codes
            codes.append(code)

        # In production, hash and store these codes securely
        return codes

    def verify_backup_code(self, code: str, stored_codes: list) -> Tuple[bool, list]:
        """Verify backup code and return updated list."""
        # In production, compare against hashed codes
        if code in stored_codes:
            # Remove used code
            updated_codes = [c for c in stored_codes if c != code]
            return True, updated_codes
        return False, stored_codes

class AuditLogger:
    """Enhanced audit logging with encryption."""

    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
        self.log_file = "audit_log.enc"

    def log_event(self, event_type: str, user_id: str, details: Dict,
                  severity: str = "INFO", ip_address: str = None) -> str:
        """Log an audit event, encrypting and appending to the audit log file."""
        event = {
            "event_id": secrets.token_hex(16),
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "severity": severity,
            "ip_address": ip_address,
            "details": details,
        }
        try:
            encrypted_line = self.security.encrypt_data(json.dumps(event))
            with open(self.log_file, "a", encoding="utf-8") as fh:
                fh.write(encrypted_line + "\n")
        except Exception:
            pass  # Never let audit logging crash the caller
        return event["event_id"]

    def get_events(self, user_id: str = None, event_type: str = None,
                   start_date: str = None, end_date: str = None) -> list:
        """Return decrypted audit events from the log file."""
        results = []
        try:
            with open(self.log_file, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(self.security.decrypt_data(line))
                    except Exception:
                        continue
                    if user_id and event.get("user_id") != user_id:
                        continue
                    if event_type and event.get("event_type") != event_type:
                        continue
                    if start_date and event.get("timestamp", "") < start_date:
                        continue
                    if end_date and event.get("timestamp", "") > end_date:
                        continue
                    results.append(event)
        except FileNotFoundError:
            pass
        return results

class DataEncryption:
    """Field-level encryption for sensitive data."""

    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager

    def encrypt_field(self, value: str, field_name: str) -> str:
        """Encrypt a specific field."""
        if not value:
            return value

        # Add field context for additional security
        data_to_encrypt = f"{field_name}:{value}"
        return self.security.encrypt_data(data_to_encrypt)

    def decrypt_field(self, encrypted_value: str, field_name: str) -> str:
        """Decrypt a specific field."""
        if not encrypted_value:
            return encrypted_value

        try:
            decrypted = self.security.decrypt_data(encrypted_value)
            # Verify field context
            if decrypted.startswith(f"{field_name}:"):
                return decrypted[len(field_name) + 1:]
            else:
                raise ValueError("Field context mismatch")
        except Exception:
            raise ValueError("Failed to decrypt field")

    def encrypt_supplier_data(self, supplier_data: Dict) -> Dict:
        """Encrypt sensitive fields in supplier data."""
        encrypted_data = supplier_data.copy()

        # Fields that should be encrypted
        sensitive_fields = [
            "contact_email", "contact_phone", "bank_account",
            "tax_id", "social_security", "credit_card"
        ]

        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt_field(encrypted_data[field], field)

        return encrypted_data

    def decrypt_supplier_data(self, encrypted_data: Dict) -> Dict:
        """Decrypt sensitive fields in supplier data."""
        decrypted_data = encrypted_data.copy()

        sensitive_fields = [
            "contact_email", "contact_phone", "bank_account",
            "tax_id", "social_security", "credit_card"
        ]

        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt_field(decrypted_data[field], field)
                except ValueError:
                    # If decryption fails, keep encrypted value
                    pass

        return decrypted_data

# Global instances
_security_manager = None
_mfa_manager = None
_audit_logger = None
_data_encryption = None

def get_security_manager() -> SecurityManager:
    """Get global security manager instance."""
    global _security_manager
    if _security_manager is None:
        try:
            _security_manager = SecurityManager()
        except ImportError as e:
            raise ImportError(f"Security manager unavailable: {e}")
    return _security_manager

def get_mfa_manager() -> MFAManager:
    """Get global MFA manager instance."""
    global _mfa_manager
    if _mfa_manager is None:
        try:
            _mfa_manager = MFAManager()
        except ImportError as e:
            raise ImportError(f"MFA manager unavailable: {e}")
    return _mfa_manager

def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(get_security_manager())
    return _audit_logger

def get_data_encryption() -> DataEncryption:
    """Get global data encryption instance."""
    global _data_encryption
    if _data_encryption is None:
        _data_encryption = DataEncryption(get_security_manager())
    return _data_encryption

# Convenience functions
def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data."""
    return get_security_manager().encrypt_data(data)

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data."""
    return get_security_manager().decrypt_data(encrypted_data)

def setup_mfa_for_user(user_id: str) -> Dict:
    """Set up MFA for a user."""
    mfa = get_mfa_manager()
    secret = mfa.generate_secret(user_id)
    uri = mfa.get_totp_uri(secret, user_id)
    backup_codes = mfa.generate_backup_codes(user_id)

    return {
        "secret": secret,
        "totp_uri": uri,
        "backup_codes": backup_codes
    }

def verify_mfa_code(user_id: str, code: str, secret: str) -> bool:
    """Verify MFA code for a user."""
    return get_mfa_manager().verify_totp(secret, code)
