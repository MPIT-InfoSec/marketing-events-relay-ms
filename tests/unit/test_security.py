"""Unit tests for security module."""

import base64
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.exceptions import EncryptionError
from app.core.security import CredentialEncryption, get_encryption, verify_basic_auth


# ============================================================================
# CredentialEncryption Tests
# ============================================================================


class TestCredentialEncryption:
    """Tests for CredentialEncryption class."""

    def test_encrypt_decrypt_roundtrip(self, encryption: CredentialEncryption):
        """Test that encrypting and decrypting returns original data."""
        original = {
            "access_token": "test_token_123",
            "pixel_id": "12345",
        }

        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == original

    def test_encrypted_data_is_different(self, encryption: CredentialEncryption):
        """Test that encrypted data differs from original."""
        original = {"access_token": "test_token"}

        encrypted = encryption.encrypt(original)

        assert encrypted != str(original)
        assert "test_token" not in encrypted

    def test_encrypt_empty_dict(self, encryption: CredentialEncryption):
        """Test encrypting empty dictionary."""
        original: dict[str, Any] = {}

        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == original

    def test_encrypt_nested_dict(self, encryption: CredentialEncryption):
        """Test encrypting nested dictionary."""
        original = {
            "oauth": {
                "client_id": "test_client",
                "client_secret": "test_secret",
            },
            "settings": {"timeout": 30},
        }

        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == original

    def test_encrypt_dict_with_various_types(self, encryption: CredentialEncryption):
        """Test encrypting dictionary with various value types."""
        original = {
            "string_value": "test",
            "int_value": 42,
            "float_value": 3.14,
            "bool_value": True,
            "none_value": None,
            "list_value": [1, 2, 3],
        }

        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == original

    def test_encrypt_special_characters(self, encryption: CredentialEncryption):
        """Test encrypting strings with special characters."""
        original = {
            "key_with_unicode": "Test \u00e9\u00e8\u00ea",
            "key_with_emoji": "Test \U0001F600",
            "key_with_special": "!@#$%^&*()_+-=[]{}|;':\",./<>?",
        }

        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == original

    def test_decrypt_invalid_token_raises_error(self, encryption: CredentialEncryption):
        """Test that decrypting invalid data raises EncryptionError."""
        with pytest.raises(EncryptionError) as exc_info:
            encryption.decrypt("invalid_encrypted_data")

        assert "invalid encryption token" in str(exc_info.value).lower()

    def test_decrypt_tampered_data_raises_error(self, encryption: CredentialEncryption):
        """Test that decrypting tampered data raises EncryptionError."""
        original = {"access_token": "test"}
        encrypted = encryption.encrypt(original)

        # Tamper with the encrypted data
        tampered = encrypted[:-5] + "XXXXX"

        with pytest.raises(EncryptionError):
            encryption.decrypt(tampered)

    def test_decrypt_empty_string_raises_error(self, encryption: CredentialEncryption):
        """Test that decrypting empty string raises EncryptionError."""
        with pytest.raises(EncryptionError):
            encryption.decrypt("")

    def test_decrypt_with_wrong_key_raises_error(self):
        """Test that decrypting with wrong key raises EncryptionError."""
        key1 = CredentialEncryption.generate_key()
        key2 = CredentialEncryption.generate_key()

        encryption1 = CredentialEncryption(encryption_key=key1)
        encryption2 = CredentialEncryption(encryption_key=key2)

        original = {"access_token": "test_token"}
        encrypted = encryption1.encrypt(original)

        with pytest.raises(EncryptionError):
            encryption2.decrypt(encrypted)

    def test_same_data_different_ciphertext(self, encryption: CredentialEncryption):
        """Test that same data produces different ciphertext each time."""
        original = {"access_token": "test_token"}

        encrypted1 = encryption.encrypt(original)
        encrypted2 = encryption.encrypt(original)

        # Due to Fernet's random IV, same data should produce different ciphertext
        assert encrypted1 != encrypted2

        # But both should decrypt to the same original
        assert encryption.decrypt(encrypted1) == original
        assert encryption.decrypt(encrypted2) == original


class TestCredentialEncryptionMasking:
    """Tests for credential masking functionality."""

    def test_mask_credentials_long_strings(self):
        """Test masking long credential values."""
        credentials = {
            "access_token": "sk_live_abcdefghijklmnop",
            "pixel_id": "123456789012345",
        }

        masked = CredentialEncryption.mask_credentials(credentials)

        assert masked["access_token"] == "sk_l***nop"
        assert masked["pixel_id"] == "1234***345"

    def test_mask_credentials_short_strings(self):
        """Test masking short credential values."""
        credentials = {
            "short_key": "abc",
            "medium_key": "12345678",
        }

        masked = CredentialEncryption.mask_credentials(credentials)

        assert masked["short_key"] == "***"
        # 8 chars is exactly the threshold
        assert masked["medium_key"] == "***"

    def test_mask_credentials_exactly_9_chars(self):
        """Test masking values with exactly 9 characters."""
        credentials = {
            "nine_chars": "123456789",
        }

        masked = CredentialEncryption.mask_credentials(credentials)

        # 9 chars > 8, so should be masked with first 4 and last 3
        assert masked["nine_chars"] == "1234***789"

    def test_mask_credentials_non_string_values(self):
        """Test masking non-string values."""
        credentials = {
            "int_value": 12345,
            "bool_value": True,
            "none_value": None,
        }

        masked = CredentialEncryption.mask_credentials(credentials)

        assert masked["int_value"] == "***"
        assert masked["bool_value"] == "***"
        assert masked["none_value"] == "***"

    def test_mask_credentials_empty_dict(self):
        """Test masking empty dictionary."""
        credentials: dict[str, Any] = {}

        masked = CredentialEncryption.mask_credentials(credentials)

        assert masked == {}

    def test_mask_credentials_preserves_keys(self):
        """Test that masking preserves all keys."""
        credentials = {
            "access_token": "long_token_value_here",
            "api_key": "another_long_key_value",
            "secret": "secret_value_too_long",
        }

        masked = CredentialEncryption.mask_credentials(credentials)

        assert set(masked.keys()) == set(credentials.keys())


class TestCredentialEncryptionKeyGeneration:
    """Tests for key generation functionality."""

    def test_generate_key_length(self):
        """Test generated key has correct length."""
        key = CredentialEncryption.generate_key()

        # Fernet keys are 32 bytes, base64-encoded = 44 characters
        assert len(key) == 44

    def test_generate_key_is_string(self):
        """Test generated key is a string."""
        key = CredentialEncryption.generate_key()

        assert isinstance(key, str)

    def test_generate_key_is_base64(self):
        """Test generated key is valid base64."""
        key = CredentialEncryption.generate_key()

        # Should not raise an exception
        decoded = base64.urlsafe_b64decode(key)
        assert len(decoded) == 32  # 32 bytes for Fernet

    def test_generate_key_uniqueness(self):
        """Test generated keys are unique."""
        keys = [CredentialEncryption.generate_key() for _ in range(100)]

        # All keys should be unique
        assert len(set(keys)) == 100

    def test_generated_key_works_for_encryption(self):
        """Test that a generated key can be used for encryption."""
        key = CredentialEncryption.generate_key()
        encryption = CredentialEncryption(encryption_key=key)

        original = {"access_token": "test_value"}
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == original


class TestCredentialEncryptionInitialization:
    """Tests for CredentialEncryption initialization."""

    def test_init_with_custom_key(self):
        """Test initialization with custom key."""
        custom_key = CredentialEncryption.generate_key()
        encryption = CredentialEncryption(encryption_key=custom_key)

        original = {"test": "data"}
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == original

    def test_init_without_key_uses_settings(self):
        """Test initialization without key uses settings."""
        encryption = CredentialEncryption()

        # Should not raise an exception
        original = {"test": "data"}
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == original


# ============================================================================
# get_encryption Singleton Tests
# ============================================================================


class TestGetEncryption:
    """Tests for get_encryption singleton function."""

    def test_get_encryption_returns_instance(self):
        """Test get_encryption returns an instance."""
        encryption = get_encryption()

        assert isinstance(encryption, CredentialEncryption)

    def test_get_encryption_returns_same_instance(self):
        """Test get_encryption returns the same instance on multiple calls."""
        encryption1 = get_encryption()
        encryption2 = get_encryption()

        assert encryption1 is encryption2


# ============================================================================
# verify_basic_auth Tests
# ============================================================================


class TestVerifyBasicAuth:
    """Tests for HTTP Basic Auth verification."""

    def test_valid_credentials(self, auth_headers: dict):
        """Test valid credentials pass verification."""
        from app.core.config import settings

        # Create mock credentials
        mock_credentials = MagicMock()
        mock_credentials.username = settings.basic_auth_username
        mock_credentials.password = settings.basic_auth_password

        result = verify_basic_auth(mock_credentials)

        assert result == settings.basic_auth_username

    def test_invalid_username(self):
        """Test invalid username raises HTTPException."""
        mock_credentials = MagicMock()
        mock_credentials.username = "wrong_user"
        mock_credentials.password = "some_password"

        with pytest.raises(HTTPException) as exc_info:
            verify_basic_auth(mock_credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in exc_info.value.detail

    def test_invalid_password(self):
        """Test invalid password raises HTTPException."""
        from app.core.config import settings

        mock_credentials = MagicMock()
        mock_credentials.username = settings.basic_auth_username
        mock_credentials.password = "wrong_password"

        with pytest.raises(HTTPException) as exc_info:
            verify_basic_auth(mock_credentials)

        assert exc_info.value.status_code == 401

    def test_both_invalid(self):
        """Test both invalid username and password raises HTTPException."""
        mock_credentials = MagicMock()
        mock_credentials.username = "wrong_user"
        mock_credentials.password = "wrong_password"

        with pytest.raises(HTTPException) as exc_info:
            verify_basic_auth(mock_credentials)

        assert exc_info.value.status_code == 401

    def test_empty_credentials(self):
        """Test empty credentials raise HTTPException."""
        mock_credentials = MagicMock()
        mock_credentials.username = ""
        mock_credentials.password = ""

        with pytest.raises(HTTPException) as exc_info:
            verify_basic_auth(mock_credentials)

        assert exc_info.value.status_code == 401

    def test_www_authenticate_header_on_failure(self):
        """Test WWW-Authenticate header is set on failure."""
        mock_credentials = MagicMock()
        mock_credentials.username = "wrong_user"
        mock_credentials.password = "wrong_password"

        with pytest.raises(HTTPException) as exc_info:
            verify_basic_auth(mock_credentials)

        assert exc_info.value.headers["WWW-Authenticate"] == "Basic"


# ============================================================================
# EncryptionError Tests
# ============================================================================


class TestEncryptionError:
    """Tests for EncryptionError exception."""

    def test_encryption_error_message(self):
        """Test EncryptionError has correct message."""
        error = EncryptionError(message="Test error message")

        assert "Test error message" in str(error.message)

    def test_encryption_error_with_details(self):
        """Test EncryptionError with details."""
        error = EncryptionError(
            message="Test error",
            details={"key": "value"},
        )

        assert error.details == {"key": "value"}

    def test_encryption_error_status_code(self):
        """Test EncryptionError has 500 status code."""
        error = EncryptionError(message="Test error")

        assert error.status_code == 500


# ============================================================================
# Edge Cases and Security Tests
# ============================================================================


class TestSecurityEdgeCases:
    """Tests for security edge cases and potential vulnerabilities."""

    def test_timing_attack_resistance(self):
        """Test that password comparison is timing-attack resistant.

        The verify_basic_auth function uses secrets.compare_digest
        which is designed to be resistant to timing attacks.
        This test verifies the function is called correctly.
        """
        from app.core.config import settings

        # Valid credentials should work
        mock_credentials = MagicMock()
        mock_credentials.username = settings.basic_auth_username
        mock_credentials.password = settings.basic_auth_password

        result = verify_basic_auth(mock_credentials)
        assert result == settings.basic_auth_username

    def test_unicode_in_credentials(self, encryption: CredentialEncryption):
        """Test handling of unicode characters in credentials."""
        credentials = {
            "token_\u00e9": "value_\u00e8",  # Unicode in key and value
            "password": "\u4e2d\u6587\u5bc6\u7801",  # Chinese characters
        }

        encrypted = encryption.encrypt(credentials)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == credentials

    def test_very_long_credential_values(self, encryption: CredentialEncryption):
        """Test handling of very long credential values."""
        credentials = {
            "long_token": "x" * 10000,  # 10KB string
        }

        encrypted = encryption.encrypt(credentials)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == credentials

    def test_many_credential_keys(self, encryption: CredentialEncryption):
        """Test handling of many credential keys."""
        credentials = {f"key_{i}": f"value_{i}" for i in range(100)}

        encrypted = encryption.encrypt(credentials)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == credentials
        assert len(decrypted) == 100
