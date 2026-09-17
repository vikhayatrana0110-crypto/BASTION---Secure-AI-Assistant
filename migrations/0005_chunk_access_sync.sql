CREATE POLICY documents_owner_all ON documents FOR ALL TO bastion_worker
USING (true) WITH CHECK (true);

CREATE POLICY chunks_owner_all ON chunks FOR ALL TO bastion_worker
USING (true) WITH CHECK (true);

CREATE FUNCTION chunks_copy_access() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    SELECT d.department, d.min_level
    INTO NEW.department, NEW.min_level
    FROM documents d
    WHERE d.id = NEW.document_id;
    RETURN NEW;
END;
$$; 

CREATE TRIGGER chunks_copy_access
BEFORE INSERT OR UPDATE OF document_id, department, min_level ON chunks
FOR EACH ROW EXECUTE FUNCTION chunks_copy_access();

CREATE FUNCTION documents_sync_chunk_access() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    UPDATE chunks
       SET department = NEW.department,
           min_level  = NEW.min_level
     WHERE document_id = NEW.id;
    RETURN NULL;
END;
$$;

CREATE TRIGGER documents_sync_chunk_access
AFTER UPDATE OF department, min_level ON documents
FOR EACH ROW
WHEN (OLD.department IS DISTINCT FROM NEW.department
      OR OLD.min_level IS DISTINCT FROM NEW.min_level)
EXECUTE FUNCTION documents_sync_chunk_access();