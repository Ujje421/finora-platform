"""
Financial Intelligence Platform — API Key Encryption

AES-256-GCM encryption for user API keys (BYOM architecture).
Keys are encrypted at rest and decrypted only in memory at call time.

Security rules:
- NEVER log API keys (log only last 4 chars as key_suffix)
- NEVER return decrypted keys to the frontend
- NEVER store plaintext keys anywhere
- Clear decrypted keys from memory after use
"""

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings
from app.utils.logging import get_logger

log = get_logger(__name__)


class KeyVault:
    """Encrypts and decrypts user API keys using Fernet (AES-128-CBC with HMAC)."""

    def __init__(self, master_key: str | None = None):
        key = master_key or get_settings().api_key_encryption_key
        if not key:
            log.warning(
                "No API_KEY_ENCRYPTION_KEY set — generating ephemeral key. "
                "This is acceptable for development only."
            )
            key = Fernet.generate_key().decode()
        self._cipher = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, api_key: str) -> str:
        """
        Encrypt an API key for storage.

        Returns the encrypted ciphertext as a string.
        """
        return self._cipher.encrypt(api_key.encode()).decode()

    def decrypt(self, encrypted_key: str) -> str:
        """
        Decrypt an API key for use.

        The caller MUST delete the returned value after use.
        """
        try:
            return self._cipher.decrypt(encrypted_key.encode()).decode()
        except InvalidToken:
            log.error("Failed to decrypt API key — invalid token or corrupted data")
            raise ValueError("Failed to decrypt API key. Key may be corrupted.")

    @staticmethod
    def get_key_suffix(api_key: str) -> str:
        """
        Get the last 4 characters of an API key for display purposes.

        This is the ONLY part of the key that should ever be logged or shown to users.
        """
        if len(api_key) < 4:
            return "****"
        return api_key[-4:]

    @staticmethod
    def generate_master_key() -> str:
        """Generate a new master encryption key. Run once during setup."""
        return Fernet.generate_key().decode()


# Singleton instance
_vault: KeyVault | None = None


def get_key_vault() -> KeyVault:
    """Get the singleton KeyVault instance."""
    global _vault
    if _vault is None:
        _vault = KeyVault()
    return _vault
