CREATE FUNCTION app_access_scope() RETURNS text
LANGUAGE sql STABLE AS $$
    SELECT app_level()::text || ':' ||
           array_to_string(ARRAY(SELECT unnest(app_departments()) ORDER BY 1), ',')
$$;

CREATE TABLE conversations (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      uuid NOT NULL DEFAULT app_user() REFERENCES users(id) ON DELETE CASCADE,
    access_scope text NOT NULL DEFAULT app_access_scope(),
    title        text,
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX conversations_user_id_idx ON conversations (user_id);

CREATE TABLE messages (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            text NOT NULL CHECK (role IN ('user', 'assistant')),
    content         text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX messages_conversation_id_idx ON messages (conversation_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON conversations TO bastion_app;
GRANT SELECT, INSERT, DELETE ON messages TO bastion_app;

ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations FORCE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages FORCE ROW LEVEL SECURITY;

CREATE POLICY conversations_own ON conversations FOR ALL
USING (user_id = app_user() AND access_scope = app_access_scope())
WITH CHECK (user_id = app_user() AND access_scope = app_access_scope());

CREATE POLICY messages_via_conversation ON messages FOR ALL
USING (EXISTS (SELECT 1 FROM conversations c WHERE c.id = messages.conversation_id))
WITH CHECK (EXISTS (SELECT 1 FROM conversations c WHERE c.id = messages.conversation_id));