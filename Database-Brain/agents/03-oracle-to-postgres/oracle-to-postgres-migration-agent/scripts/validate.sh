#!/usr/bin/env bash
# validate.sh — Phase 5: compare row counts between Oracle source and PG target.
# Outputs out/validation_report.txt with PASS/FAIL per table.
set -euo pipefail
cd "$(dirname "$0")/.."

: "${ORACLE_FQDN:?must be set}"
: "${ORACLE_PWD:?must be set}"
: "${PG_FQDN:?must be set}"
: "${PG_PWD:?must be set}"
: "${SCHEMA:?must be set (e.g. HR)}"

PG_SCHEMA=$(echo "$SCHEMA" | tr 'A-Z' 'a-z')
REPORT=out/validation_report.txt
mkdir -p out
: > "$REPORT"

# Oracle table list
TABLES=$(sqlplus -s "ora2pg_user/${ORACLE_PWD}@${ORACLE_FQDN}:1521/XEPDB1" <<EOF
SET HEADING OFF FEEDBACK OFF PAGESIZE 0 LINESIZE 200
SELECT table_name FROM all_tables WHERE owner = '$SCHEMA' ORDER BY table_name;
EXIT;
EOF
)

PASS=0
FAIL=0

for T in $TABLES; do
  T_LOWER=$(echo "$T" | tr 'A-Z' 'a-z')

  ORA_COUNT=$(sqlplus -s "ora2pg_user/${ORACLE_PWD}@${ORACLE_FQDN}:1521/XEPDB1" <<EOF
SET HEADING OFF FEEDBACK OFF PAGESIZE 0
SELECT count(*) FROM $SCHEMA.$T;
EXIT;
EOF
  )
  ORA_COUNT=$(echo "$ORA_COUNT" | tr -d ' \r\n')

  PG_COUNT=$(PGPASSWORD="$PG_PWD" psql -t -A \
    "host=$PG_FQDN dbname=oracle_migration user=migration_user sslmode=require" \
    -c "SELECT count(*) FROM ${PG_SCHEMA}.${T_LOWER};" 2>/dev/null || echo "ERR")

  if [ "$ORA_COUNT" = "$PG_COUNT" ]; then
    STATUS="PASS"
    PASS=$((PASS+1))
  else
    STATUS="FAIL"
    FAIL=$((FAIL+1))
  fi

  printf "[%s] %-30s oracle=%-10s pg=%-10s\n" "$STATUS" "$T" "$ORA_COUNT" "$PG_COUNT" | tee -a "$REPORT"
done

echo "" | tee -a "$REPORT"
echo "==> Summary: $PASS PASS, $FAIL FAIL" | tee -a "$REPORT"
[ "$FAIL" -eq 0 ]
