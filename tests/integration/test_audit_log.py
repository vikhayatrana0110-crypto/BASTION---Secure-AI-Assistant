import psycopg
import pytest

from bastion.config import get_settings

pytestmark = pytest.mark.integration


def delete_test_data(conn):
    conn.execute("delete from audit_log where action like 'test.%'")
    conn.execute("delete from users where email like 'audit-%@nimbus.test'")


@pytest.fixture
def users():
    settings = get_settings()

    with psycopg.connect(settings.database_url_owner) as conn:
        delete_test_data(conn)
        rows = conn.execute(
            """
            insert into users (email, password_hash, level, departments, is_admin)
            values ('audit-a@nimbus.test', 'x', 2, '{ENG}', false),
                   ('audit-b@nimbus.test', 'x', 2, '{ENG}', false),
                   ('audit-admin@nimbus.test', 'x', 2, '{HR}', true)
            returning email, id
            """
        ).fetchall()
        conn.commit()

    ids = dict(rows)
    yield {
        "a": ids["audit-a@nimbus.test"],
        "b": ids["audit-b@nimbus.test"],
        "admin": ids["audit-admin@nimbus.test"],
    }

    with psycopg.connect(settings.database_url_owner) as conn:
        delete_test_data(conn)
        conn.commit()


def set_context(conn, user_id, is_admin=False):
    conn.execute(
        "select set_config('app.user_id', %s, true), set_config('app.is_admin', %s, true)",
        (str(user_id), str(is_admin).lower()),
    )


def log_event(user_id, action):
    with psycopg.connect(get_settings().database_url_app) as conn:
        set_context(conn, user_id)
        conn.execute("insert into audit_log (action) values (%s)", (action,))


def visible_test_events(user_id, is_admin=False):
    with psycopg.connect(get_settings().database_url_app) as conn:
        set_context(conn, user_id, is_admin)
        return conn.execute(
            "select count(*) from audit_log where action like 'test.%'"
        ).fetchone()[0]


def test_users_see_only_their_own_events(users):
    log_event(users["a"], "test.query")
    log_event(users["b"], "test.query")

    assert visible_test_events(users["a"]) == 1


def test_admin_sees_every_event(users):
    log_event(users["a"], "test.query")
    log_event(users["b"], "test.query")

    assert visible_test_events(users["admin"], is_admin=True) == 2


def test_cannot_log_an_event_as_someone_else(users):
    with psycopg.connect(get_settings().database_url_app) as conn:
        set_context(conn, users["a"])

        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute(
                "insert into audit_log (user_id, action) values (%s, 'test.forged')",
                (users["b"],),
            )


@pytest.mark.parametrize(
    "statement",
    [
        "update audit_log set action = 'test.tampered'",
        "delete from audit_log",
    ],
)
def test_audit_log_cannot_be_changed_or_deleted(users, statement):
    log_event(users["a"], "test.query")

    with psycopg.connect(get_settings().database_url_app) as conn:
        set_context(conn, users["a"])

        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute(statement)