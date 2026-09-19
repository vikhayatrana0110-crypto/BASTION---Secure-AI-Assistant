import psycopg
import pytest

from bastion.auth.login import authenticate
from bastion.auth.passwords import hash_password
from bastion.config import get_settings
from bastion.db import access_tx

pytestmark = pytest.mark.integration

PASSWORD = "seed-test-password"


@pytest.fixture
def engineer_account():
    settings = get_settings()

    with psycopg.connect(settings.database_url_owner) as conn:
        conn.execute("delete from users where email ilike 'login-%@nimbus.test'")
        conn.execute("delete from documents where title like 'login-%'")
        conn.execute(
            "insert into users (email, password_hash, level, departments, is_admin)"
            " values ('Login-Eng@Nimbus.test', %s, 2, '{ENG}', false)",
            (hash_password(PASSWORD),),
        )
        conn.execute(
            "insert into documents (title, source_type, department, min_level)"
            " values ('login-runbook', 'md', 'ENG', 2), ('login-budget', 'pdf', 'FIN', 2)"
        )
        conn.commit()

    yield

    with psycopg.connect(settings.database_url_owner) as conn:
        conn.execute("delete from users where email ilike 'login-%@nimbus.test'")
        conn.execute("delete from documents where title like 'login-%'")
        conn.commit()


def test_correct_password_returns_the_users_access(engineer_account):
    access = authenticate("Login-Eng@Nimbus.test", PASSWORD)

    assert access is not None
    assert access.level == 2
    assert access.departments == ("ENG",)
    assert access.is_admin is False


def test_login_is_case_insensitive(engineer_account):
    assert authenticate("login-eng@NIMBUS.TEST", PASSWORD) is not None


def test_wrong_password_is_refused(engineer_account):
    assert authenticate("Login-Eng@Nimbus.test", "not the password") is None


def test_unknown_email_is_refused(engineer_account):
    assert authenticate("nobody@nimbus.test", PASSWORD) is None


def test_the_returned_access_is_usable_for_queries(engineer_account):
    access = authenticate("Login-Eng@Nimbus.test", PASSWORD)

    with access_tx(access) as conn:
        rows = conn.execute(
            "select title from documents where title like 'login-%' order by title"
        ).fetchall()

    assert [row[0] for row in rows] == ["login-runbook"]
