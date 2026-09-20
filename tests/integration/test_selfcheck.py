import psycopg
import pytest
from fastapi.testclient import TestClient

from bastion.config import get_settings
from bastion.db import get_pool, verify_security_invariants
from bastion.main import create_app

pytestmark = pytest.mark.integration


def test_the_real_database_passes_the_check():
    with get_pool().connection() as conn:
        verify_security_invariants(conn)


def test_a_role_that_can_bypass_rls_is_refused():
    with psycopg.connect(get_settings().database_url_owner) as conn:
        with pytest.raises(RuntimeError, match="bypass"):
            verify_security_invariants(conn)


def test_a_table_without_forced_rls_is_refused():
    with psycopg.connect(get_settings().database_url_owner) as conn:
        conn.execute("create table unprotected_probe (id int)")
        conn.commit()

    try:
        with pytest.raises(RuntimeError, match="unprotected_probe"):
            with get_pool().connection() as conn:
                verify_security_invariants(conn)
    finally:
        with psycopg.connect(get_settings().database_url_owner) as conn:
            conn.execute("drop table unprotected_probe")
            conn.commit()


def test_readyz_reports_ready():
    with TestClient(create_app()) as client:
        response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}