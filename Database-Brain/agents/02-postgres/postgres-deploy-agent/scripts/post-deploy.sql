-- =========================================================================
-- post-deploy.sql — postgres-deploy-agent
-- Run AFTER deployment: enable extensions, prep migration schemas, grants.
-- Run as the admin user defined in postgres-flex.bicep (pgadmin by default).
-- Idempotent.
-- =========================================================================

-- 1. Enable whitelisted extensions ----------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS orafce;  -- Oracle compat functions (NVL, DECODE, ...)

-- 2. Migration target database --------------------------------------------
-- Ora2Pg / DMS push their schemas into a dedicated DB to isolate from postgres meta.
SELECT 'CREATE DATABASE oracle_migration'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'oracle_migration')
\gexec

\c oracle_migration

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS orafce;

-- 3. Schemas mirroring Oracle sample schemas ------------------------------
CREATE SCHEMA IF NOT EXISTS hr;
CREATE SCHEMA IF NOT EXISTS sh;
CREATE SCHEMA IF NOT EXISTS oe;

-- 4. Migration service user (used by Ora2Pg + DMS) ------------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'migration_user') THEN
    -- Set password via \password migration_user after this script
    CREATE ROLE migration_user LOGIN PASSWORD 'CHANGE_ME_AFTER_SCRIPT';
  END IF;
END$$;

GRANT ALL ON SCHEMA hr, sh, oe TO migration_user;
GRANT ALL ON DATABASE oracle_migration TO migration_user;

-- 5. Sanity check ----------------------------------------------------------
SELECT current_database(), current_user, version();
SELECT extname FROM pg_extension ORDER BY 1;
SELECT nspname FROM pg_namespace WHERE nspname IN ('hr','sh','oe');

\echo '==> Post-deploy complete. Now run: \\password migration_user'
