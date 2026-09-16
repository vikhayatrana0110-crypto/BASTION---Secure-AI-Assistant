import psycopg
import pytest

from bastion.config import get_settings

pytestmark = pytest.mark.integration


@pytest.fixture
def seeded_documents():
    settings = get_settings()

    with psycopg.connect(settings.database_url_owner) as conn:
        conn.execute("delete from documents where title like 'acc-%'")
        conn.execute(
            """
            insert into documents (title, source_type, department, min_level, status)
            values ('acc-handbook',   'md',  'ALL', 1, 'ready'),
                   ('acc-runbook',    'md',  'ENG', 2, 'ready'),
                   ('acc-eng-secret', 'md',  'ENG', 3, 'ready'),
                   ('acc-budget',     'pdf', 'FIN', 3, 'ready')
            """
        )
        conn.commit()

    yield

    with psycopg.connect(settings.database_url_owner) as conn:
        conn.execute("delete from documents where title like 'acc-%'")
        conn.commit()


def visible_titles(level, departments, is_admin=False):
    with psycopg.connect(get_settings().database_url_app) as conn:
        conn.execute(
            "select set_config('app.user_level', %s, true),"
            " set_config('app.departments', %s, true),"
            " set_config('app.is_admin', %s, true)",
            (str(level), ",".join(departments), str(is_admin).lower()),
        )
        rows = conn.execute(
            "select title from documents where title like 'acc-%' order by title"
        ).fetchall()

    return [row[0] for row in rows]


def test_no_context_sees_nothing(seeded_documents):
    with psycopg.connect(get_settings().database_url_app) as conn:
        rows = conn.execute("select title from documents where title like 'acc-%'").fetchall()

    assert rows == []


def test_level_boundary_hides_higher_level_documents(seeded_documents):
    assert visible_titles(2, ["ENG"]) == ["acc-handbook", "acc-runbook"]


def test_department_boundary_hides_other_departments(seeded_documents):
    assert visible_titles(2, ["FIN"]) == ["acc-handbook"]


def test_executive_with_every_department_sees_all(seeded_documents):
    assert visible_titles(4, ["ENG", "HR", "FIN", "LEGAL"]) == [
        "acc-budget",
        "acc-eng-secret",
        "acc-handbook",
        "acc-runbook",
    ]


def test_admin_flag_does_not_widen_reading(seeded_documents):
    assert visible_titles(2, ["FIN"], is_admin=True) == ["acc-handbook"]


def test_non_admin_cannot_insert(seeded_documents):
    with psycopg.connect(get_settings().database_url_app) as conn:
        conn.execute(
            "select set_config('app.user_level', '4', true),"
            " set_config('app.departments', 'ENG', true),"
            " set_config('app.is_admin', 'false', true)"
        )

        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute(
                "insert into documents (title, source_type, department, min_level)"
                " values ('acc-nope', 'md', 'ENG', 1)"
            )


def test_admin_can_insert(seeded_documents):
    with psycopg.connect(get_settings().database_url_app) as conn:
        conn.execute(
            "select set_config('app.user_level', '4', true),"
            " set_config('app.departments', 'ENG', true),"
            " set_config('app.is_admin', 'true', true)"
        )
        conn.execute(
            "insert into documents (title, source_type, department, min_level)"
            " values ('acc-nope', 'md', 'ENG', 1)"
        )
        conn.rollback()