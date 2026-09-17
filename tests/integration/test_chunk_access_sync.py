import psycopg
import pytest

from bastion.config import get_settings

pytestmark = pytest.mark.integration

DOC_TITLE = "sync-test-doc"


@pytest.fixture
def document_with_chunks():
    settings = get_settings()

    with psycopg.connect(settings.database_url_owner) as conn:
        conn.execute("delete from documents where title = %s", (DOC_TITLE,))
        doc_id = conn.execute(
            "insert into documents (title, source_type, department, min_level)"
            " values (%s, 'md', 'ENG', 2) returning id",
            (DOC_TITLE,),
        ).fetchone()[0]
        conn.execute(
            """
            insert into chunks (document_id, ordinal, text, department, min_level, quarantined)
            values (%(doc)s, 0, 'normal passage', 'HR', 4, false),
                   (%(doc)s, 1, 'poisoned passage', 'HR', 4, true)
            """,
            {"doc": doc_id},
        )
        conn.commit()

    yield doc_id

    with psycopg.connect(settings.database_url_owner) as conn:
        conn.execute("delete from documents where title = %s", (DOC_TITLE,))
        conn.commit()


def chunk_access(doc_id):
    with psycopg.connect(get_settings().database_url_owner) as conn:
        return conn.execute(
            "select department, min_level from chunks where document_id = %s order by ordinal",
            (doc_id,),
        ).fetchall()


def test_chunks_copy_access_from_their_document_on_insert(document_with_chunks):
    assert chunk_access(document_with_chunks) == [("ENG", 2), ("ENG", 2)]


def test_moving_a_document_moves_every_chunk_including_quarantined(document_with_chunks):
    with psycopg.connect(get_settings().database_url_app) as conn:
        conn.execute(
            "select set_config('app.user_level', '4', true),"
            " set_config('app.departments', 'ENG,HR,FIN,LEGAL', true),"
            " set_config('app.is_admin', 'true', true)"
        )
        conn.execute(
            "update documents set department = 'FIN', min_level = 3 where id = %s",
            (document_with_chunks,),
        )
        conn.commit()

    assert chunk_access(document_with_chunks) == [("FIN", 3), ("FIN", 3)]