from datetime import UTC, datetime, timedelta

import jwt

from bastion.config import get_settings
from bastion.db import Access

ALGORITHM = "HS256"
MIN_SECRET_LENGTH = 32
TOKEN_LIFETIME = timedelta(minutes=30)

def _secret() -> str:
    secret = get_settings().jwt_secret

    if len(secret) < MIN_SECRET_LENGTH:
        raise RuntimeError(f"BASTION_JWT_SECRET must be at least {MIN_SECRET_LENGTH} characters")

    return secret

def issue_token(access: Access, token_version: int) -> str:
    now = datetime.now(UTC)

    return jwt.encode(
        {
            "sub": str(access.user_id),
            "ver": token_version,
            "iat": now,
            "exp": now + TOKEN_LIFETIME,
        },
        _secret(),
        algorithm=ALGORITHM,
    )


def read_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None