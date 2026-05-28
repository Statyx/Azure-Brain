#!/usr/bin/env bash
# run-copy-load.sh — Phase 3 (offline): direct Oracle → PG data pipe via Ora2Pg COPY.
# Run AFTER tables + sequences are applied. Idempotent (TRUNCATE_TABLE=1 in conf).
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

START=$(date +%s)
ora2pg -c "$CONF" -t COPY -j 4
END=$(date +%s)

echo ""
echo "==> Data load complete in $((END-START)) seconds."
echo "==> Now run scripts/post-load.sql to setval sequences + ANALYZE."
