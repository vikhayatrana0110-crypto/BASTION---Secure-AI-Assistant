from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from psycopg import Connection

from bastion.db.pool import get_pool

SET_CONTEXT = (
    "select set_config('app.user_id', %s, true),"
    " set_config('app.user_level', %s, true),"
    " set_config('app.departments', %s, true),"
    " set_config('app.is_admin', %s, true)"    
)

@dataclass(frozen=True)
class Access:
    user_id: str
    level: int
    departments: tuple[str,...] = ()
    is_admin: bool = False

@contextmanager
def access_tx(access: Access) -> Iterator[Connection]:
    with get_pool().connection() as conn, conn.transaction():
        conn.execute(
            SET_CONTEXT,
            (
                str(access.user_id),
                str(access.level),
                ",".join(access.departments),
                "true" if access.is_admin else "false",
            ),
        )
        yield conn