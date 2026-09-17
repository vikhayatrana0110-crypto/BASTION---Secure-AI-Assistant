import psycopg
import pytest

from bastion.config import get_settings

pytestmark = pytest.mark.integration


@pytest.fixture
def two_users():
    settings = get_settings()

    with psycopg.connect(settings.database_url_owner) as conn:
        conn.execute("delete from users where email like 'conv-%@nimbus.test'")
        rows = conn.execute(
            """
            insert into users (email, password_hash, level, departments)
            values ('conv-a@nimbus.test', 'x', 2, '{ENG,FIN}'),
                   ('conv-b@nimbus.test', 'x', 2, '{ENG,FIN}')
            returning email, id
            """
        ).fetchall()
        conn.commit()

    ids = dict(rows)
    yield {"a": ids["conv-a@nimbus.test"], "b": ids["conv-b@nimbus.test"]}

    with psycopg.connect(settings.database_url_owner) as conn:
        conn.execute("delete from users where email like 'conv-%@nimbus.test'")
        conn.commit()


def set_context(conn, user_id, level, departments):
    conn.execute(
        "select set_config('app.user_id', %s, true),"
        " set_config('app.user_level', %s, true),"
        " set_config('app.departments', %s, true)",
        (str(user_id), str(level), ",".join(departments)),
    )


def start_conversation(user_id, level, departments):
    with psycopg.connect(get_settings().database_url_app) as conn:
        set_context(conn, user_id, level, departments)
        conversation_id = conn.execute(
            "insert into conversations (title) values ('test chat') returning id"
        ).fetchone()[0]
        conn.execute(
            "insert into messages (conversation_id, role, content)"
            " values (%s, 'user', 'hello')",
            (conversation_id,),
        )


def visible_counts(user_id, level, departments):
    with psycopg.connect(get_settings().database_url_app) as conn:
        set_context(conn, user_id, level, departments)
        return conn.execute(
            "select (select count(*) from conversations), (select count(*) from messages)"
        ).fetchone()


def test_owner_sees_their_conversation_and_its_messages(two_users):
    start_conversation(two_users["a"], 2, ["ENG", "FIN"])

    assert visible_counts(two_users["a"], 2, ["FIN", "ENG"]) == (1, 1)


def test_another_user_with_identical_access_sees_nothing(two_users):
    start_conversation(two_users["a"], 2, ["ENG", "FIN"])

    assert visible_counts(two_users["b"], 2, ["ENG", "FIN"]) == (0, 0)


def test_history_disappears_when_access_shrinks(two_users):
    start_conversation(two_users["a"], 2, ["ENG", "FIN"])

    assert visible_counts(two_users["a"], 2, ["ENG"]) == (0, 0)


def test_cannot_start_a_conversation_as_someone_else(two_users):
    with psycopg.connect(get_settings().database_url_app) as conn:
        set_context(conn, two_users["a"], 2, ["ENG", "FIN"])

        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute(
                "insert into conversations (user_id, title) values (%s, 'forged')",
                (two_users["b"],),
            )