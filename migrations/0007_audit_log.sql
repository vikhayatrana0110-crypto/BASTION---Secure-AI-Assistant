CREATE TABLE audit_log (
    id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id    uuid DEFAULT app_user() REFERENCES users(id) ON DELETE SET NULL,
    action     text NOT NULL,
    detail     jsonb NOT NULL DEFAULT '{}',
    tokens_in  int,
    tokens_out int,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX audit_log_user_id_idx ON audit_log (user_id);
CREATE INDEX audit_log_created_at_idx ON audit_log (created_at);

GRANT SELECT, INSERT ON audit_log TO bastion_app;
GRANT INSERT ON audit_log TO bastion_worker;

ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log FORCE ROW LEVEL SECURITY;

CREATE POLICY audit_log_insert ON audit_log FOR INSERT
WITH CHECK (user_id IS NOT DISTINCT FROM app_user());

CREATE POLICY audit_log_read ON audit_log FOR SELECT
USING (user_id = app_user() OR app_is_admin());