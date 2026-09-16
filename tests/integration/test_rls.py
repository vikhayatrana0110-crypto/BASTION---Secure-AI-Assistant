import psycopg
import pytest

from bastion.config import get_settings

pytestmark = pytest.mark.integration

@pytest.fixture
def seeded_users():
    settings = get_settings()

    with psycopg.connect(settings.database_url_owner) as conn:
        conn.execute("delete from users where email like 'rls-%@nimbus.test'")
        rows = conn.execute(
            """
            insert into users (email, password_hash, level, departments, is_admin)
            values ('rls-intern@nimbus.test', 'x', 1, '{ENG}', false),
                   ('rls-cfo@nimbus.test', 'x', 4, '{ENG,HR,FIN,LEGAL}', true)
            returning id
            """
        ).fetchall()
        conn.commit()

    yield [row[0] for row in rows]

    with psycopg.connect(settings.database_url_owner) as conn:
        conn.execute("delete from users where email like 'rls-%@nimbus.test'")
        conn.commit()

def test_app_role_sees_nothing_without_context(seeded_users):
    with psycopg.connect(get_settings().database_url_app) as conn:
        rows = conn.execute("select id from users").fetchall()

    assert rows == []


def test_app_role_sees_only_its_own_row(seeded_users):
    _, cfo_id = seeded_users

    with psycopg.connect(get_settings().database_url_app) as conn:
        conn.execute("select set_config('app.user_id', %s, true)", (str(cfo_id),))
        rows = conn.execute("select id from users").fetchall()

    assert [row[0] for row in rows] == [cfo_id]


def test_context_does_not_leak_into_the_next_transaction(seeded_users):
    _, cfo_id = seeded_users

    with psycopg.connect(get_settings().database_url_app) as conn:
        conn.execute("select set_config('app.user_id', %s, true)", (str(cfo_id),))
        assert conn.execute("select count(*) from users").fetchone()[0] == 1
        conn.commit()

        assert conn.execute("select count(*) from users").fetchone()[0] == 0