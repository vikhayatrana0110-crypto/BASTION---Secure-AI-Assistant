import psycopg

PRIVILEGE_CHECK = """
select rolsuper, rolbypassrls
  from pg_roles
 where rolname = current_user
"""

# schema_migrations is excluded on purpose: only the owner touches it and the app
# holds no grants on it, so row level rules would protect nothing.
UNPROTECTED_TABLES = """
select c.relname
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public'
   and c.relkind = 'r'
   and c.relname <> 'schema_migrations'
   and not (c.relrowsecurity and c.relforcerowsecurity)
 order by c.relname
"""


def verify_security_invariants(conn: psycopg.Connection) -> None:
    is_superuser, can_bypass_rls = conn.execute(PRIVILEGE_CHECK).fetchone()

    if is_superuser or can_bypass_rls:
        raise RuntimeError("the app must not connect as a role that can bypass row-level security")

    unprotected = [row[0] for row in conn.execute(UNPROTECTED_TABLES).fetchall()]

    if unprotected:
        raise RuntimeError(f"tables without FORCE ROW LEVEL SECURITY: {', '.join(unprotected)}")