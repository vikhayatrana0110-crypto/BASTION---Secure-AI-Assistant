CREATE POLICY users_owner_all ON users FOR ALL TO bastion_owner
USING (true) WITH CHECK (true);

CREATE FUNCTION auth_lookup(p_email text)
RETURNS TABLE (id uuid, password_hash text, level int, departments text[],
               is_admin boolean, token_version int)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT u.id, u.password_hash, u.level, u.departments, u.is_admin, u.token_version
      FROM users u
     WHERE lower(u.email) = lower(p_email)
$$;

REVOKE ALL ON FUNCTION auth_lookup(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION auth_lookup(text) TO bastion_app;