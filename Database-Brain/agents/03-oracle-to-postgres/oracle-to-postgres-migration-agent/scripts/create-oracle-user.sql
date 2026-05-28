-- create-oracle-user.sql
-- Create a read-only user for Ora2Pg on the source Oracle XE.
-- Connect as SYS: sqlplus sys/<pw>@<fqdn>:1521/XEPDB1 as sysdba
-- Run: SQL> @create-oracle-user.sql <password>

DEFINE ora2pg_pwd = '&1';

CREATE USER ora2pg_user IDENTIFIED BY "&ora2pg_pwd";

-- Minimum privileges required by Ora2Pg
GRANT CONNECT TO ora2pg_user;
GRANT SELECT_CATALOG_ROLE TO ora2pg_user;
GRANT SELECT ANY DICTIONARY TO ora2pg_user;
GRANT SELECT ANY TABLE TO ora2pg_user;

-- Read-only access to sample schemas
GRANT SELECT ANY TABLE TO ora2pg_user;
GRANT SELECT ANY SEQUENCE TO ora2pg_user;

-- For PL/SQL extraction (functions, packages)
GRANT EXECUTE ANY PROCEDURE TO ora2pg_user;

EXIT;
