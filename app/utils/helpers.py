import hashlib
import secrets

from app.config.settings import get_settings

settings = get_settings()


def _hash_secret(secret: str) -> str:
    salt = secrets.token_bytes(16)

    digest = hashlib.pbkdf2_hmac(
        settings.PASSWORD_HASH_ALGORITHM,
        secret.encode("utf-8"),
        salt,
        settings.PASSWORD_HASH_ITERATIONS,
    )

    return (
        f"{settings.PASSWORD_HASH_SCHEME}"
        f"${settings.PASSWORD_HASH_ITERATIONS}"
        f"${salt.hex()}"
        f"${digest.hex()}"
    )


def _verify_secret(secret: str, stored_value: str) -> bool:
    try:
        scheme, iterations, salt_hex, stored_hash = stored_value.split("$")
        if scheme != settings.PASSWORD_HASH_SCHEME:
            return False
        salt = bytes.fromhex(salt_hex)
        digest = hashlib.pbkdf2_hmac(
            settings.PASSWORD_HASH_ALGORITHM,
            secret.encode("utf-8"),
            salt,
            int(iterations),
        )
        return secrets.compare_digest(digest.hex(), stored_hash)
    except (TypeError, ValueError):
        return False


def _hash_password(password: str) -> str:
    return _hash_secret(password)


def _verify_password(password: str, stored_password: str) -> bool:
    return _verify_secret(password, stored_password)
    

characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

def _generate_email_code() -> str:
    """Generate an 8-character, URL-safe email verification code."""
    return "".join(secrets.choice(characters) for _ in range(8))
