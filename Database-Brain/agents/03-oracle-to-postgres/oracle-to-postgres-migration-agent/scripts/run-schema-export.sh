#!/usr/bin/env bash
# run-schema-export.sh — Phase 2: export Oracle DDL as PostgreSQL DDL.
# Generates out/{tables,sequences,indexes,triggers,functions,views}.sql
set -euo pipefail
cd "$(dirname "$0")/.."

: "${ORACLE_FQDN:?must be set}"
: "${ORACLE_PWD:?must be set}"
: "${PG_FQDN:?must be set}"
: "${PG_PWD:?must be set}"

CONF=out/ora2pg.conf
if [ ! -f "$CONF" ]; then
  echo "Run scripts/run-assessment.sh first to render $CONF" >&2; exit 1
fi

for OBJ in TABLE SEQUENCE INDEX TRIGGER FUNCTION VIEW; do
  OUT="out/$(echo $OBJ | tr 'A-Z' 'a-z')s.sql"
  echo "==> Exporting $OBJ to $OUT"
  ora2pg -c "$CONF" -t "$OBJ" -o "$OUT"
done

echo ""
echo "==> Schema export complete."
echo "==> REVIEW out/functions.sql and out/triggers.sql MANUALLY (PL/SQL conversion is 70-85% accurate)."
echo "==> Then apply in order:"
echo "     psql ... -f out/tables.sql"
echo "     psql ... -f out/sequences.sql"
echo "     (load data via scripts/run-copy-load.sh)"
echo "     psql ... -f out/indexes.sql"
echo "     psql ... -f out/triggers.sql"
echo "     psql ... -f out/views.sql"
