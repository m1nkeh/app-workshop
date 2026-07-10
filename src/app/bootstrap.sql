-- Lakebase one-time admin bootstrap for the receipts app.
--
-- Run ONCE per Lakebase branch by a project owner / databricks_superuser, on
-- your own connection (databricks psql, or the SQL editor). NOT part of the
-- migrations. Replace the group names and identities with yours.

CREATE EXTENSION IF NOT EXISTS databricks_auth;


-- === Section A: roles + membership -- run BEFORE `alembic upgrade head` ========

-- Sync the Databricks groups into Postgres roles.
SELECT databricks_create_role('receipts-app-owner-dev', 'GROUP');
SELECT databricks_create_role('receipts-app-readwrite-dev', 'GROUP');

-- The owner group creates the schema/tables (migrations SET ROLE to it), so it
-- needs CREATE on the database.
GRANT CREATE ON DATABASE databricks_postgres TO "receipts-app-owner-dev";

-- REQUIRED and easy to miss: let migration runners SET ROLE to the owner group.
-- databricks_create_role enrols the creator with set_option = false (because
-- createrole_self_grant is empty), so without this, migrations fail at their
-- first `SET ROLE` with "permission denied to set role". INHERIT lets you read
-- owner-owned objects (e.g. alembic_version) as yourself.
GRANT "receipts-app-owner-dev" TO "chris.thompson@databricks.com" WITH SET TRUE, INHERIT TRUE;
-- GRANT "receipts-app-owner-dev" TO "<ci-cd-sp-client-id>" WITH SET TRUE, INHERIT TRUE;


-- === Section B: read/write for the app -- run AFTER `alembic upgrade head` =====

-- App users and the app SP inherit read/write via membership in the rw group,
-- never a direct grant to the SP. INHERIT so the privileges apply when they
-- connect as themselves.
GRANT "receipts-app-readwrite-dev" TO "chris.thompson@databricks.com" WITH INHERIT TRUE;
-- GRANT "receipts-app-readwrite-dev" TO "<app-sp-client-id>" WITH INHERIT TRUE;

-- Grant the rw group its privileges, acting as the owner so the defaults are
-- attributed to the owner (which owns app + its tables).
SET ROLE "receipts-app-owner-dev";
GRANT USAGE ON SCHEMA app TO "receipts-app-readwrite-dev";
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA app TO "receipts-app-readwrite-dev";
ALTER DEFAULT PRIVILEGES IN SCHEMA app
    GRANT SELECT, INSERT, UPDATE ON TABLES TO "receipts-app-readwrite-dev";
RESET ROLE;
