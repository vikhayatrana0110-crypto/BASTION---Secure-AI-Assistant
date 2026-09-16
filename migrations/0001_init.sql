CREATE EXTENSION IF NOT EXISTS vector;

CREATE FUNCTION app_user() RETURNS uuid
LANGUAGE sql STABLE AS $$
    SELECT NULLIF(current_setting('app.user_id', true), '')::uuid
$$;

CREATE FUNCTION app_level() RETURNS int
LANGUAGE sql STABLE AS $$
    SELECT NULLIF(current_setting('app.user_level', true), '')::int
$$;

CREATE FUNCTION app_departments() RETURNS text[]
LANGUAGE sql STABLE AS $$
    SELECT string_to_array(NULLIF(current_setting('app.departments', 
true), ''), ',')
$$;

CREATE FUNCTION app_is_admin() RETURNS boolean
LANGUAGE sql STABLE AS $$
    SELECT COALESCE(NULLIF(current_setting('app.is_admin', true), 
'')::boolean, false)
$$;

CREATE TABLE users (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),          
    email         text NOT NULL UNIQUE,
    password_hash text NOT NULL,
    level         int NOT NULL CHECK (level BETWEEN 1 AND 4),
    departments   text[] NOT NULL DEFAULT '{}',
    is_admin      boolean NOT NULL DEFAULT false,
    token_version int NOT NULL DEFAULT 0,
    created_at    timestamptz NOT NULL DEFAULT now()
);

GRANT SELECT ON users to bastion_app, bastion_worker;
