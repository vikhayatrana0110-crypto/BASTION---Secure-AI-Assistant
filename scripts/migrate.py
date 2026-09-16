import pathlib
import sys

import psycopg

from bastion.config import get_settings

MIGRATIONS_DIR = pathlib.Path(__file__).resolve().parent.parent / "migrations"

TRACKING_TABLE = """
create table if not exists schema_migrations (
    filename   text primary key,
    applied_at timestamptz not null default now()
)
"""


def main() -> int:
    with psycopg.connect(get_settings().database_url_owner) as conn:
        conn.execute(TRACKING_TABLE)
        conn.commit()

        applied = {row[0] for row in conn.execute("select filename from schema_migrations")}

        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in applied:
                print(f"skip    {path.name}")
                continue

            conn.execute(path.read_text())
            conn.execute("insert into schema_migrations (filename) values (%s)", (path.name,))
            conn.commit()
            print(f"applied {path.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())