from bastion.auth.passwords import hash_password, verify_password
from bastion.auth.tokens import read_token
from bastion.db import Access, get_pool

_DUMMY_HASH = hash_password("bastion-dummy-password")

LOOKUP = (
    "select id, password_hash, level, departments, is_admin, token_version"
    " from auth_lookup(%s)"
)


def authenticate(email: str, password: str) -> Access | None:
    with get_pool().connection() as conn:
        row = conn.execute(LOOKUP, (email,)).fetchone()

    if row is None:
        verify_password(password, _DUMMY_HASH)
        return None

    user_id, password_hash, level, departments, is_admin, _token_version = row

    if not verify_password(password, password_hash):
        return None

    return Access(
        user_id=user_id,
        level=level,
        departments=tuple(departments),
        is_admin=is_admin,
    )


LOOKUP_BY_ID = (
    "select id, level, departments, is_admin, token_version from auth_lookup_by_id(%s)"
)


def access_for_token(token: str) -> Access | None:
    claims = read_token(token)

    if claims is None:
        return None

    with get_pool().connection() as conn:
        row = conn.execute(LOOKUP_BY_ID, (claims["sub"],)).fetchone()

    if row is None:
        return None

    user_id, level, departments, is_admin, token_version = row

    if token_version != claims["ver"]:
        return None

    return Access(
        user_id=user_id,
        level=level,
        departments=tuple(departments),
        is_admin=is_admin,
    )