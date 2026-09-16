CREATE TABLE documents (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title          text NOT NULL,
    source_type    text NOT NULL CHECK (source_type IN ('md', 'html', 'pdf', 'docx', 'slack')),
    department     text NOT NULL CHECK (department IN ('ALL', 'ENG', 'HR', 'FIN', 'LEGAL')),
    min_level      int NOT NULL CHECK (min_level BETWEEN 1 AND 4),
    effective_date date,
    storage_key    text,
    content_hash   text,
    version        int NOT NULL DEFAULT 1,
    status         text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'ready', 'failed')),
    created_at     timestamptz NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON documents TO bastion_app;
GRANT SELECT, INSERT, UPDATE ON documents TO bastion_worker;

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents FORCE ROW LEVEL SECURITY;

CREATE POLICY documents_read ON documents FOR SELECT
USING (
    current_user = 'bastion_worker'
    OR (
        min_level <= app_level() 
        AND (department = 'ALL' OR department = ANY(app_departments()))
    )
);

CREATE POLICY documents_insert ON documents FOR INSERT
WITH CHECK (current_user = 'bastion_worker' OR app_is_admin());

CREATE POLICY documents_update ON documents FOR UPDATE
USING (current_user = 'bastion_worker' OR app_is_admin())
WITH CHECK (current_user = 'bastion_worker' OR app_is_admin());

CREATE POLICY documents_delete ON documents FOR DELETE
USING (app_is_admin());


