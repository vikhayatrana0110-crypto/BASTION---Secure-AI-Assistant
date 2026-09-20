CREATE FUNCTION auth_lookup_by_id(p_user_id uuid)
RETURNS TABLE (id uuid, level int, departments text[], is_admin boolean, token_version int)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
    SELECT u.id, u.level, u.departments, u.is_admin, u.token_version
      FROM users u
     WHERE u.id = p_user_id
$$;

REVOKE ALL ON FUNCTION auth_lookup_by_id(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION auth_lookup_by_id(uuid) TO bastion_app;