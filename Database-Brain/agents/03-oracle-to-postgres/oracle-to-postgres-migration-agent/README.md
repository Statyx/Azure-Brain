# Quickstart — oracle-to-postgres-migration-agent

End-to-end Oracle XE → Azure DB for PostgreSQL migration in ~30 min.

## Prerequisites

1. Oracle source deployed via [oracle-source-vm-agent](../oracle-source-vm-agent/README.md) — sample schemas loaded
2. PG target deployed via [postgres-deploy-agent](../../02-postgres/postgres-deploy-agent/README.md) — `oracle_migration` DB + `migration_user` ready
3. Linux jumpbox with network access to both (or use the Oracle VM itself)

## 0. Install Ora2Pg on the jumpbox (one-shot)

```bash
sudo bash scripts/install-ora2pg.sh
ora2pg --version  # expect 25.0+
```

## 1. Create read-only Ora2Pg user on Oracle

```bash
ORACLE_FQDN=vm-oracle-src.francecentral.cloudapp.azure.com
ORACLE_SYS_PWD=$(cat .oracle-syspw.txt)        # from oracle-source-vm-agent
ORA2PG_PWD=$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)

sqlplus "sys/${ORACLE_SYS_PWD}@${ORACLE_FQDN}:1521/XEPDB1 as sysdba" \
  @scripts/create-oracle-user.sql "${ORA2PG_PWD}"
```

## 2. Set env

```bash
export ORACLE_FQDN=vm-oracle-src.francecentral.cloudapp.azure.com
export ORACLE_PWD=$ORA2PG_PWD
export PG_FQDN=pg-ora-target-abc123.postgres.database.azure.com
export PG_PWD=$(cat ../../02-postgres/postgres-deploy-agent/.pgadmin-pw.txt)
export SCHEMA=HR
```

## 3. Phase 1 — Assessment

```bash
bash scripts/run-assessment.sh
# Open out/migration_report.html in browser
```

Report shows:
- Total Oracle objects (tables, views, indexes, packages, ...)
- Complexity score (A / B / C — A = easy, C = manual rewrite required)
- Estimated person-days for manual refactor
- Compatibility breakdown per object type

## 4. Phase 2 — Schema export

```bash
bash scripts/run-schema-export.sh
ls out/   # tables.sql sequences.sql indexes.sql triggers.sql functions.sql views.sql

# Review PL/SQL conversions manually (the 70-85% accuracy zone)
less out/functions.sql
less out/triggers.sql
```

Apply schema (without indexes/triggers — they slow data load):

```bash
PGPASSWORD=$PG_PWD psql "host=$PG_FQDN dbname=oracle_migration user=migration_user sslmode=require" \
  -f out/tables.sql \
  -f out/sequences.sql
```

## 5. Phase 3 — Data load (offline cutover)

```bash
bash scripts/run-copy-load.sh
# Direct Oracle → PG pipe, ~918k rows of SH.SALES in ~2-5 min
```

## 6. Phase 4 — Post-load fixups

```bash
PGPASSWORD=$PG_PWD psql "host=$PG_FQDN dbname=oracle_migration user=migration_user sslmode=require" \
  -f scripts/post-load.sql

# Now apply indexes + triggers + views (much faster after data is in)
PGPASSWORD=$PG_PWD psql "host=$PG_FQDN dbname=oracle_migration user=migration_user sslmode=require" \
  -f out/indexes.sql \
  -f out/triggers.sql \
  -f out/views.sql
```

## 7. Phase 5 — Validate

```bash
bash scripts/validate.sh
# Output: PASS/FAIL per table, summary at end
```

## Repeat for SH and OE schemas

```bash
SCHEMA=SH bash scripts/run-assessment.sh
# ... (duplicate config snippet with SCHEMA=SH, PG_SCHEMA=sh)
```

For multi-schema demos, copy `config/ora2pg.conf` to `config/ora2pg.sh.conf` and `config/ora2pg.oe.conf`, then point each run to its config file.

## Online cutover (NOT for Oracle XE)

If you swap the XE source for Oracle Enterprise Edition on Azure VM with ARCHIVELOG mode:

```bash
# Use Azure DMS instead of Ora2Pg COPY for phase 3
az dms project task create \
  --service-name dms-ora2pg \
  --project-name oracle-to-pg \
  --task-type OfflineMigration \
  --resource-group $RG \
  --task-name initial-load \
  --task-options-json @dms-task.json
```

Online cutover with CDC requires Oracle EE + GoldenGate or LogMiner — out of scope for this XE demo.
