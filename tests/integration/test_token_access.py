import psycopg
import pytest

from bastion.auth.login import access_for_token
from bastion.auth.tokens import issue_token
from bastion.config import get_settings
from bastion.db import Access

pytestmark = pytest.mark.integration

EMAIL = "token-test@nimbus.test"


@pytest.fixture
def account(monkeypatch):
    monkeypatch.setenv("BASTION_JWT_SECRET", "t" * 40)
    get_settings.cache_clear()
    settings = get_settings()

    with psycopg.connect(settings.database_url_owner) as conn:
        conn.execute("delete from users where email ilike %s", (EMAIL,))
        user_id = conn.execute(
            "insert into users (email, password_hash, level, departments, is_admin)"
            " values (%s, 'x', 2, '{ENG}', false) returning id",
            (EMAIL,),
        ).fetchone()[0]
        conn.commit()

    yield user_id

    with psycopg.connect(settings.database_url_owner) as conn:
        conn.execute("delete from users where email ilike %s", (EMAIL,))
        conn.commit()

    get_settings.cache_clear()


def set_level(user_id, level):
    with psycopg.connect(get_settings().database_url_owner) as conn:
        conn.execute("update users set level = %s where id = %s", (level, user_id))
        conn.commit()


def set_token_version(user_id, version):
    with psycopg.connect(get_settings().database_url_owner) as conn:
        conn.execute("update users set token_version = %s where id = %s", (version, user_id))
        conn.commit()


def token_for(user_id, token_version=0):
    access = Access(user_id=user_id, level=2, departments=("ENG",))
    return issue_token(access, token_version=token_version)


def test_a_valid_token_gives_the_users_current_access(account):
    access = access_for_token(token_for(account))

    assert access is not None
    assert access.level == 2
    assert access.departments == ("ENG",)


def test_access_reflects_a_demotion_immediately(account):
    token = token_for(account)
    set_level(account, 1)

    access = access_for_token(token)

    assert access.level == 1
    set_token_version(account, 1)

def test_bumping_token_version_ends_the_session(account):
    token = token_for(account)
    set_token_version(account, 1)

    assert access_for_token(token) is None


def test_a_deleted_user_has_no_access(account):
    token = token_for(account)

    with psycopg.connect(get_settings().database_url_owner) as conn:
        conn.execute("delete from users where id = %s", (account,))
        conn.commit()

    assert access_for_token(token) is None


def test_a_garbage_token_has_no_access(account):
    assert access_for_token("not.a.token") is None