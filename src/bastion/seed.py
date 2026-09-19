import os
import sys

import psycopg

from bastion.auth.passwords import hash_password
from bastion.config import get_settings

PERSONAS = [
    ("intern@nimbus.test", 1, ["ENG"], False),
    ("engineer@nimbus.test", 2, ["ENG"], False),
    ("eng.manager@nimbus.test", 3, ["ENG"], False),
    ("hr.specialist@nimbus.test", 2, ["HR"], False),
    ("hr.manager@nimbus.test", 3, ["HR"], False),
    ("finance.analyst@nimbus.test", 2, ["FIN"], False),
    ("legal.counsel@nimbus.test", 3, ["LEGAL"], False),
    ("cfo@nimbus.test", 4, ["ENG", "HR", "FIN", "LEGAL"], True),
]

UPSERT = """
insert into users (email, password_hash, level, departments, is_admin)
values (%s, %s, %s, %s, %s)
on conflict (email) do update
   set password_hash = excluded.password_hash,
       level         = excluded.level,
       departments   = excluded.departments,
       is_admin      = excluded.is_admin
"""


def seed_personas(conn: psycopg.Connection, password: str) -> int:
    for email, level, departments, is_admin in PERSONAS:
        conn.execute(UPSERT, (email, hash_password(password), level, departments, is_admin))

    return len(PERSONAS)


def main() -> int:
    password = os.environ.get("BASTION_SEED_PASSWORD")
    if not password:
        print("BASTION_SEED_PASSWORD is not set")
        return 1

    with psycopg.connect(get_settings().database_url_owner) as conn:
        count = seed_personas(conn, password)
        conn.commit()

    print(f"seeded {count} personas")
    return 0


if __name__ == "__main__":
    sys.exit(main())