import jwt

from app.config import get_settings
from app.main import app
from app.utils.auth import create_access_token
from app.utils.helpers import _generate_email_code, _hash_password, _verify_password


def test_documented_routes_are_in_openapi() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/user/create" in paths
    assert "/api/v1/user/verify" in paths
    assert "/api/v1/user/login" in paths
    assert "/api/v1/user/me" in paths


def test_password_hash_verification_and_malformed_hash() -> None:
    password = "a sufficiently long test password"
    stored_password = _hash_password(password)

    assert _verify_password(password, stored_password)
    assert not _verify_password("incorrect", stored_password)
    assert not _verify_password(password, "invalid")


def test_verification_code_has_expected_shape() -> None:
    code = _generate_email_code()
    assert len(code) == 8
    assert code.isalnum()


def test_access_token_contains_subject() -> None:
    settings = get_settings()
    token = create_access_token(123)
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == "123"
