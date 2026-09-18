from functools import lru_cache

from psycopg_pool import ConnectionPool

from bastion.config import get_settings


@lru_cache
def get_pool() -> ConnectionPool:
    return ConnectionPool(get_settings().database_url_app, min_size=1, max_size=10, open=True)