from datetime import timedelta
import uuid

from app.core.security import create_jwt, decode_jwt, hash_password, hash_opaque_token, verify_password


def test_passwords_are_argon2_hashes_and_verify_correctly() -> None:
    password_hash = hash_password("Seguro123!")
    assert password_hash.startswith("$argon2")
    assert verify_password("Seguro123!", password_hash)
    assert not verify_password("incorrecta", password_hash)


def test_opaque_tokens_are_hashed_deterministically() -> None:
    assert hash_opaque_token("refresh-token") == hash_opaque_token("refresh-token")
    assert hash_opaque_token("refresh-token") != hash_opaque_token("other-token")


def test_jwt_contains_subject_and_type() -> None:
    user_id = uuid.uuid4()
    token = create_jwt(user_id, "access", timedelta(minutes=5))
    claims = decode_jwt(token, "access")
    assert claims["sub"] == str(user_id)
    assert claims["type"] == "access"

