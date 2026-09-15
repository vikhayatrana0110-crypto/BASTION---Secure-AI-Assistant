import psycopg
import pytest

from bastion.config import get_settings

pytestmark = pytest.mark.integration

def test_database_is_reachable():
    with psycopg.connect(get_settings().database_url_owner,connect_timeout=5) as conn:
        version = conn.execute("show server_version_num").fetchone()[0]

    assert int(version) >= 170000

def test_pgvector_is_available():
    with psycopg.connect(get_settings().database_url_owner,connect_timeout=5) as conn:
            row = conn.execute("select default_version from pg_available_extensions where name =" \
            " 'vector'"
            ).fetchone()

    assert row is not None