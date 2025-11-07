"""
Encryption service for securing sensitive data (passwords, connection strings).

Uses AES-256 symmetric encryption to encrypt/decrypt sensitive database
credentials before storage.
"""

import os
from cryptography.fernet import Fernet
from typing import Optional


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data using Fernet (AES-128).

    Uses a symmetric encryption key from the environment (ENCRYPTION_KEY).
    The key should be a URL-safe base64-encoded 32-byte key.

    Usage:
        cipher = EncryptionService()
        encrypted_password = cipher.encrypt("MySecretPassword123")
        decrypted_password = cipher.decrypt(encrypted_password)

    Attributes:
        key: Fernet key for encryption/decryption
        cipher: Fernet cipher instance
    """

    def __init__(self, key: Optional[str] = None):
        """
        Initialize encryption service with key from environment or parameter.

        Args:
            key: Optional encryption key. If not provided, uses ENCRYPTION_KEY env var.

        Raises:
            ValueError: If no key provided and ENCRYPTION_KEY not set
            ValueError: If key is not valid base64
        """
        if key is None:
            key = os.getenv("ENCRYPTION_KEY")

        if not key:
            raise ValueError(
                "No encryption key provided. Set ENCRYPTION_KEY environment variable "
                "or pass key parameter. Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )

        try:
            # Key should be base64-encoded
            self.key = key.encode() if isinstance(key, str) else key
            self.cipher = Fernet(self.key)
        except Exception as e:
            raise ValueError(f"Invalid encryption key format: {e}")

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string using Fernet symmetric encryption.

        Args:
            plaintext: String to encrypt (e.g., password, connection string)

        Returns:
            Base64-encoded encrypted string

        Example:
            encrypted = service.encrypt("my_password_123")
            # Returns: "gAAAAABlx...encoded_string...xyz"
        """
        if not plaintext:
            return ""

        plaintext_bytes = plaintext.encode("utf-8")
        encrypted_bytes = self.cipher.encrypt(plaintext_bytes)
        encrypted_str = encrypted_bytes.decode("utf-8")

        return encrypted_str

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext using Fernet symmetric decryption.

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            InvalidToken: If ciphertext is invalid or tampered
            ValueError: If decryption fails

        Example:
            plaintext = service.decrypt(encrypted)
            # Returns: "my_password_123"
        """
        if not ciphertext:
            return ""

        try:
            ciphertext_bytes = ciphertext.encode("utf-8")
            plaintext_bytes = self.cipher.decrypt(ciphertext_bytes)
            plaintext = plaintext_bytes.decode("utf-8")

            return plaintext
        except Exception as e:
            raise ValueError(f"Decryption failed (possible key mismatch or tampering): {e}")

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key for use.

        Returns:
            Base64-encoded URL-safe encryption key

        Usage:
            key = EncryptionService.generate_key()
            print(f"Add to .env: ENCRYPTION_KEY={key}")
        """
        return Fernet.generate_key().decode("utf-8")


# Global encryption service instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """
    Get or create global encryption service instance (singleton pattern).

    Returns:
        EncryptionService: Global encryption service instance

    Raises:
        ValueError: If ENCRYPTION_KEY environment variable is not set
    """
    global _encryption_service

    if _encryption_service is None:
        _encryption_service = EncryptionService()

    return _encryption_service
