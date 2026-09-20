import psycopg
import pytest

from bastion.auth.login import authenticate
from bastion.config import get_settings
from bastion.seed import PERSONAS, seed_personas

pytestmark = pytest.mark.integration

PASSWORD = "seed-test-password"


@pytest.fixture
def seeded():
    emails = [email for email, *_ in PERSONAS]

    with psycopg.connect(get_settings().database_url_owner) as conn:
        before = conn.execute(
            "select email, password_hash from users where email = any(%s)", (emails,)
        ).fetchall()
        seed_personas(conn, PASSWORD)
        conn.commit()

    yield

    with psycopg.connect(get_settings().database_url_owner) as conn:
        for email, password_hash in before:
            conn.execute(
                "update users set password_hash = %s where email = %s", (password_hash, email)
            )
        conn.commit()


def test_every_persona_can_log_in_with_the_expected_access(seeded):
    for email, level, departments, is_admin in PERSONAS:
        access = authenticate(email, PASSWORD)

        assert access is not None, email
        assert access.level == level, email
        assert access.departments == tuple(departments), email
        assert access.is_admin is is_admin, email


def test_seeding_twice_does_not_duplicate_anyone(seeded):
    emails = [email for email, *_ in PERSONAS]

    with psycopg.connect(get_settings().database_url_owner) as conn:
        seed_personas(conn, PASSWORD)
        conn.commit()
        count = conn.execute(
            "select count(*) from users where email = any(%s)", (emails,)
        ).fetchone()[0]

    assert count == len(PERSONAS)