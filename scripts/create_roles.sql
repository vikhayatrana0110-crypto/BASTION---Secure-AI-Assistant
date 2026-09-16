-- Run once per database server, as the owner. Not a migration:
-- roles live on the server, not inside the database.

CREATE ROLE bastion_app 
    LOGIN 
    PASSWORD 'bastion_app' 
    NOBYPASSRLS
    NOSUPERUSER 
    NOCREATEDB 
    NOCREATEROLE;

CREATE ROLE bastion_worker 
    LOGIN 
    PASSWORD 'bastion_worker' 
    NOBYPASSRLS
    NOSUPERUSER 
    NOCREATEDB 
    NOCREATEROLE;

GRANT CONNECT ON Database bastion TO bastion_app, bastion_worker;
GRANT USAGE ON SCHEMA public TO bastion_app, bastion_worker;