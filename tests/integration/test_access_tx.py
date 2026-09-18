import psycopg
import pytest

from bastion.config import get_settings
from bastion.db import Access, access_tx, get_pool

pytestmark = pytest.mark.integration


@pytest.fixture
def engineer():
    settings = get_settings()

    with psycopg.connect(settings.database_url_owner) as conn:
        conn.execute("delete from users where email like 'tx-%@nimbus.test'")
        conn.execute("delete from documents where title like 'tx-%'")
        user_id = conn.execute(
            "insert into users (email, password_hash, level, departments)"
            " values ('tx-eng@nimbus.test', 'x', 2, '{ENG}') returning id"
        ).fetchone()[0]
        conn.execute(
            "insert into documents (title, source_type, department, min_level)"
            " values ('tx-runbook', 'md', 'ENG', 2), ('tx-budget', 'pdf', 'FIN', 2)"
        )
        conn.commit()

    yield Access(user_id=user_id, level=2, departments=("ENG",))

    with psycopg.connect(settings.database_url_owner) as conn:
        conn.execute("delete from users where email like 'tx-%@nimbus.test'")
        conn.execute("delete from documents where title like 'tx-%'")
        conn.execute("delete from audit_log where action like 'tx.%'")
        conn.commit()


def test_access_tx_applies_the_callers_access(engineer):
    with access_tx(engineer) as conn:
        rows = conn.execute(
            "select title from documents where title like 'tx-%' order by title"
        ).fetchall()

    assert [row[0] for row in rows] == ["tx-runbook"]


def test_context_is_gone_once_the_connection_is_reused(engineer):
    with access_tx(engineer) as conn:
        inside = conn.execute(
            "select count(*) from documents where title like 'tx-%'"
        ).fetchone()[0]

    with get_pool().connection() as conn:
        afterwards = conn.execute(
            "select count(*) from documents where title like 'tx-%'"
        ).fetchone()[0]

    assert inside == 1
    assert afterwards == 0


def test_changes_roll_back_when_the_block_raises(engineer):
    with pytest.raises(RuntimeError), access_tx(engineer) as conn:
        conn.execute("insert into audit_log (action) values ('tx.event')")
        raise RuntimeError("something went wrong")

    with psycopg.connect(get_settings().database_url_owner) as conn:
        written = conn.execute(
            "select count(*) from audit_log where action = 'tx.event'"
        ).fetchone()[0]

    assert written == 0