#!/bin/bash
echo "==GRANT=="
docker exec -i oracle-xe sqlplus -s sys/Demo_Ora2Pg_2026!@//localhost:1521/XEPDB1 as sysdba <<'SQL'
GRANT SELECT_CATALOG_ROLE TO petclinic;
GRANT SELECT ANY DICTIONARY TO petclinic;
GRANT CREATE SYNONYM TO petclinic;
GRANT EXECUTE ON DBMS_METADATA TO petclinic;
EXIT;
SQL
echo "==DONE=="
