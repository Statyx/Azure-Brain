#!/usr/bin/env bash
# run-assessment.sh — Phase 1: Ora2Pg complexity report.
# Output: out/migration_report.html
set -euo pipefail
cd "$(dirname "$0")/.."

: "${ORACLE_FQDN:?must be set}"
: "${ORACLE_PWD:?must be set}"
: "${PG_FQDN:?must be set}"
: "${PG_PWD:?must be set}"

mkdir -p out

# Render config from template
sed -e "s|__ORACLE_FQDN__|$ORACLE_FQDN|g" \
    -e "s|__ORACLE_PWD__|$ORACLE_PWD|g" \
    -e "s|__PG_FQDN__|$PG_FQDN|g" \
    -e "s|__PG_PWD__|$PG_PWD|g" \
    config/ora2pg.conf > out/ora2pg.conf

ora2pg \
  -c out/ora2pg.conf \
  -t SHOW_REPORT \
  --estimate_cost \
  --dump_as_html \
  > out/migration_report.html

echo "==> Report ready: out/migration_report.html"
echo "==> Open in browser to review complexity scoring + person-days estimate."
