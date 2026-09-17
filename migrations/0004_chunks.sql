CREATE TABLE chunks (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    ordinal      int  NOT NULL,
    text         text NOT NULL,
    heading_path text[] NOT NULL DEFAULT '{}',
    page_start   int,
    department   text NOT NULL CHECK (department IN ('ALL', 'ENG', 'HR', 'FIN', 'LEGAL')),
    min_level    int  NOT NULL CHECK (min_level BETWEEN 1 AND 4),
    quarantined  boolean NOT NULL DEFAULT false,
    embedding    vector(384),
    tsv          tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    created_at   timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_id, ordinal)
);

CREATE INDEX chunks_document_id_idx ON chunks (document_id);
CREATE INDEX chunks_tsv_idx ON chunks USING gin (tsv);
CREATE INDEX chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);

GRANT SELECT, UPDATE ON chunks TO bastion_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON chunks TO bastion_worker;

ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks FORCE ROW LEVEL SECURITY;

CREATE POLICY chunks_read ON chunks FOR SELECT
USING (
    current_user = 'bastion_worker'
    OR (
        min_level <= app_level()
        AND (department = 'ALL' OR department = ANY (app_departments()))
        AND NOT quarantined
    )
);

CREATE POLICY chunks_worker_write ON chunks FOR ALL TO bastion_worker
USING (true) WITH CHECK (true);

CREATE POLICY chunks_admin_update ON chunks FOR UPDATE
USING (app_is_admin()) WITH CHECK (app_is_admin());