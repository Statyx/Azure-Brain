# oracle-to-postgres-migration-agent

## Role

End-to-end **Oracle → Azure Database for PostgreSQL** migration:
**assessment → schema conversion → data export → cutover**.

Combines two complementary tools — picks the right one per phase:

| Phase | Tool | Why |
|---|---|---|
| 1. Assessment | **Ora2Pg** | Generates HTML complexity report — number of objects, estimated migration days, refactor backlog |
| 2. Schema conversion | **Ora2Pg** | Translates DDL + PL/SQL → PL/pgSQL. Honest about what it can't translate. |
| 3. One-shot data export | **Ora2Pg COPY mode** | Direct Oracle → Postgres pipe via `COPY FROM STDIN`. Fastest for offline cutovers. |
| 4. Continuous replication + cutover | **Azure DMS** | Online mode via Oracle LogMiner / GoldenGate, minimal downtime |

Choose phase 3 OR phase 4 — not both. Phase 3 = offline cutover (acceptable downtime). Phase 4 = online (minutes of downtime).

## Hard rules

1. **Always start with assessment**. Skipping Ora2Pg `--type SHOW_REPORT` is the #1 reason demos derail mid-conversion.
2. **Ora2Pg version**: `25.0` minimum (Oct 2024+) — adds proper Oracle 21c XE support and pgvector mapping.
3. **Oracle source connection**: read-only user, NOT SYS. Create dedicated `ora2pg_user` with `SELECT ANY DICTIONARY` + `SELECT_CATALOG_ROLE`. NEVER point Ora2Pg at SYS.
4. **Schema scope**: one schema per Ora2Pg run. `SCHEMA HR` in config, not "all schemas". Running global = unbounded export, runs for hours.
5. **PL/SQL translation accuracy is 70-85%**. Anything with `CONNECT BY`, hierarchical queries, package state, autonomous transactions, or analytic gaps requires manual rewrite. The agent FLAGS these in the report — does not silently skip.
6. **DMS Oracle source requires**: ARCHIVELOG mode + `supplemental_log_data` enabled + LogMiner privileges. XE does NOT support archivelog → DMS Online mode is **NOT available with Oracle XE**. For demo with XE, use **Ora2Pg COPY mode** (phase 3 only).
7. **Encoding**: Oracle WE8MSWIN1252 → PG `UTF8`. Ora2Pg handles via `NLS_LANG = AMERICAN_AMERICA.AL32UTF8` env var. Forgetting this corrupts French accents.
8. **Sequences last**: import sequences AFTER data load, with `setval()` to current MAX(id) — otherwise next insert collides.
9. **No DDL in target before load**: let Ora2Pg create tables. Pre-creating tables → constraint conflicts on COPY.

## Workflow

```
┌──────────────────────────────────────────────────────────────────┐
│ Phase 1 — Assessment                                             │
│   ora2pg -t SHOW_REPORT --estimate_cost -c ora2pg.conf           │
│   → migration_report.html (complexity, backlog, person-days)     │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 2 — Schema export                                          │
│   ora2pg -t TABLE   -o tables.sql                                │
│   ora2pg -t SEQUENCE -o sequences.sql                            │
│   ora2pg -t INDEX   -o indexes.sql                               │
│   ora2pg -t TRIGGER -o triggers.sql  (review manually)           │
│   ora2pg -t FUNCTION -o functions.sql (review manually)          │
│   ora2pg -t VIEW    -o views.sql                                 │
│   psql -f tables.sql; psql -f sequences.sql                      │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                ┌─────────────┴────────────┐
                ▼                          ▼
┌──────────────────────────┐  ┌──────────────────────────────────┐
│ Phase 3 (offline)        │  │ Phase 3-bis (online, NOT for XE) │
│ Ora2Pg COPY              │  │ Azure DMS                        │
│ ora2pg -t COPY -j 4      │  │ Initial load + CDC               │
│   (parallel jobs)        │  │ Cutover when lag = 0             │
└──────────────────────────┘  └──────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 4 — Post-load                                              │
│   psql -f indexes.sql       (after data — much faster)           │
│   psql -f triggers.sql                                           │
│   SELECT setval('seq_name', MAX(id)) FROM table_name;            │
│   ANALYZE;                                                       │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 5 — Validation                                             │
│   Row counts per table (Oracle vs PG)                            │
│   Checksum per table (md5 of ordered concat)                     │
│   Smoke test sample app queries                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Inputs (config-driven)

The agent reads [config/ora2pg.conf](config/ora2pg.conf):

| Key | Demo value | Notes |
|---|---|---|
| `ORACLE_DSN` | `dbi:Oracle:host=<fqdn>;port=1521;sid=XEPDB1` | Service name, not SID, when 21c PDB |
| `ORACLE_USER` | `ora2pg_user` | Read-only user, NOT SYS |
| `ORACLE_PWD` | `${ORACLE_PWD}` | env var — never hardcoded |
| `PG_DSN` | `dbi:Pg:dbname=oracle_migration;host=<pg-fqdn>` | Created by postgres-deploy-agent |
| `PG_USER` | `migration_user` | |
| `PG_PWD` | `${PG_PWD}` | env var |
| `SCHEMA` | `HR` | One schema per config file. Duplicate config for HR / SH / OE. |
| `JOBS` | `4` | Parallel COPY jobs — match vCPU count of source VM |
| `DATA_LIMIT` | `10000` | Rows per batch — increase for large tables |
| `STOP_ON_ERROR` | `1` | Fail fast in demo |
| `PG_NUMERIC_TYPE` | `1` | Map Oracle NUMBER → smallest PG numeric type |
| `PG_INTEGER_TYPE` | `1` | Map Oracle NUMBER(N,0) → INTEGER / BIGINT |
| `NLS_LANG` | `AMERICAN_AMERICA.AL32UTF8` | UTF-8 export |
| `DISABLE_TRIGGERS` | `1` | Disable triggers during data load |
| `TRUNCATE_TABLE` | `1` | Idempotent re-runs |

## Files in this agent folder

- [instructions.md](instructions.md) — this file
- [README.md](README.md) — quickstart
- [config/ora2pg.conf](config/ora2pg.conf) — template config (HR schema)
- [scripts/install-ora2pg.sh](scripts/install-ora2pg.sh) — install Ora2Pg + Perl dependencies on Linux jumpbox
- [scripts/create-oracle-user.sql](scripts/create-oracle-user.sql) — create `ora2pg_user` on source
- [scripts/run-assessment.sh](scripts/run-assessment.sh) — phase 1
- [scripts/run-schema-export.sh](scripts/run-schema-export.sh) — phase 2
- [scripts/run-copy-load.sh](scripts/run-copy-load.sh) — phase 3 (offline)
- [scripts/post-load.sql](scripts/post-load.sql) — phase 4 (sequences setval, ANALYZE)
- [scripts/validate.sh](scripts/validate.sh) — row count + checksum comparison

## Common pitfalls

- **Service name vs SID**: Oracle 21c XE PDB requires service name `XEPDB1`, not SID. `dbi:Oracle:host=...;service_name=XEPDB1` not `;sid=XEPDB1` — the latter connects to CDB root which has no user data.
- **Ora2Pg ignores trailing slashes in PL/SQL**: rewrites `END procedure_name;\n/` to `END procedure_name;\n;` causing PG parse errors. Fix: `sed -i 's/;\n;/;/g' functions.sql`.
- **Oracle DATE → PG TIMESTAMP**: Oracle DATE has time. Setting `DATA_TYPE` mapping `DATE:DATE` loses time. Default mapping (DATE → TIMESTAMP) is correct — don't override.
- **HR.EMPLOYEES.COMMISSION_PCT NULL handling**: NUMBER(2,2) with NULLs becomes PG NUMERIC(2,2) but Oracle stores 0.40 as ".4" — Ora2Pg adds leading zero correctly. If you see ".4" in PG → upgrade Ora2Pg.
- **Sequences without setval**: forgetting `setval()` after data load → next INSERT fails with PK conflict on first generated value.
- **DMS + Oracle XE**: not supported. Demo with XE MUST use Ora2Pg COPY (offline cutover). For online cutover demo, point at Oracle EE on Azure VM with ARCHIVELOG enabled.
- **Easy Connect for ALL python clients** (validate.sh, any python-oracledb script): use `oracledb.connect(user="u", password="p", dsn="host:1521/XEPDB1")` — passing a TNS alias raises `DPY-4027: no configuration directory specified`. Ora2Pg (Perl DBI) is unaffected — its `ORACLE_DSN` already uses the right format.
- **Password with `!` in env vars**: bash history-expands `!` inside double quotes. Wrap with **single quotes**: `export ORACLE_PWD='P!ssw0rd'`. Then in `ora2pg.conf` substitution scripts, use `sed -i "s|__ORACLE_PWD__|${ORACLE_PWD}|g"` (the `|` delimiter avoids escaping `/` in base64-style passwords).
- **`DPY-6005` during connectivity test**: VM is up, listener is up, but Oracle instance is down (common after VM stop/start without `lifecycle/stop-vm.sh`). SSH in and `systemctl start oracle-xe-21c` to recover. Long-term: confirm `oracle-source-vm-agent` Hard rule #11 is enforced.

## Validation checklist

- [ ] Row counts match per table: `SELECT count(*) FROM hr.employees;` returns same value in Oracle and PG
- [ ] Sequences advanced: `SELECT last_value FROM hr.employees_seq;` >= MAX(employee_id)
- [ ] All triggers + indexes present in target
- [ ] Migration report HTML reviewed, manual refactor backlog logged

## Related agents

- [oracle-source-vm-agent](../oracle-source-vm-agent/instructions.md) — source environment
- [postgres-deploy-agent](../../02-postgres/postgres-deploy-agent/instructions.md) — target environment
