"""Security utilities: Basic Auth and Fernet encryption."""

import base64
import json
import secrets
from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import settings
from app.core.exceptions import AuthenticationError, EncryptionError

# HTTP Basic Auth
security = HTTPBasic()


def verify_basic_auth(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    """Verify HTTP Basic Auth credentials."""
    correct_username = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        settings.basic_auth_username.encode("utf-8"),
    )
    correct_password = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        settings.basic_auth_password.encode("utf-8"),
    )

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


class CredentialEncryption:
    """Handles encryption and decryption of credential data using Fernet."""

    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize with encryption key from settings or provided key."""
        key = encryption_key or settings.encryption_key
        if not key:
            # Generate a key if not provided (for development only)
            key = Fernet.generate_key().decode()
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, credentials: dict[str, Any]) -> str:
        """
        Encrypt credentials dictionary to a string.

        Args:
            credentials: Dictionary of credential key-value pairs

        Returns:
            Base64-encoded encrypted string

        Raises:
            EncryptionError: If encryption fails
        """
        try:
            json_bytes = json.dumps(credentials, separators=(",", ":")).encode("utf-8")
            encrypted = self._fernet.encrypt(json_bytes)
            return encrypted.decode("utf-8")
        except Exception as e:
            raise EncryptionError(
                message=f"Failed to encrypt credentials: {str(e)}",
                details={"error_type": type(e).__name__},
            )

    def decrypt(self, encrypted: str) -> dict[str, Any]:
        """
        Decrypt encrypted string to credentials dictionary.

        Args:
            encrypted: Base64-encoded encrypted string

        Returns:
            Decrypted credentials dictionary

        Raises:
            EncryptionError: If decryption fails
        """
        try:
            decrypted = self._fernet.decrypt(encrypted.encode("utf-8"))
            return json.loads(decrypted.decode("utf-8"))
        except InvalidToken:
            raise EncryptionError(
                message="Invalid encryption token - key may have changed",
                details={"error_type": "InvalidToken"},
            )
        except json.JSONDecodeError as e:
            raise EncryptionError(
                message="Decrypted data is not valid JSON",
                details={"error_type": "JSONDecodeError", "detail": str(e)},
            )
        except Exception as e:
            raise EncryptionError(
                message=f"Failed to decrypt credentials: {str(e)}",
                details={"error_type": type(e).__name__},
            )

    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet encryption key."""
        return Fernet.generate_key().decode("utf-8")

    @staticmethod
    def mask_credentials(credentials: dict[str, Any]) -> dict[str, str]:
        """
        Mask credential values for safe display.

        Args:
            credentials: Dictionary of credential key-value pairs

        Returns:
            Dictionary with masked values (e.g., "sk_live_xxx" -> "sk_l***xxx")
        """
        masked = {}
        for key, value in credentials.items():
            if isinstance(value, str) and len(value) > 8:
                masked[key] = f"{value[:4]}***{value[-3:]}"
            elif isinstance(value, str):
                masked[key] = "***"
            else:
                masked[key] = "***"
        return masked


# Singleton instance
_encryption: Optional[CredentialEncryption] = None


def get_encryption() -> CredentialEncryption:
    """Get or create encryption instance."""
    global _encryption
    if _encryption is None:
        _encryption = CredentialEncryption()
    return _encryption
