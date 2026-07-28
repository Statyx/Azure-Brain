# Oracle → PostgreSQL — Dialect & Type Reference

Cross-agent reference for Oracle → Azure Database for PostgreSQL migrations.
**Workflows live in the agents** ([`agents/03-oracle-to-postgres/`](agents/03-oracle-to-postgres/));
this file holds the reusable dialect knowledge those workflows depend on.

---

## Hard platform constraints (verified)

| Constraint | Consequence |
| --- | --- |
| Oracle **XE** does not support ARCHIVELOG | **Azure DMS Online mode is unavailable** with XE. Offline cutover via Ora2Pg `COPY` is the only path. For an online-cutover demo you need Oracle EE on a VM with ARCHIVELOG + supplemental logging. |
| Ora2Pg minimum version **25.0** (Oct 2024+) | Earlier builds lack proper Oracle 21c XE support and pgvector mapping. |
| Ora2Pg source user must **not** be `SYS` | Use a dedicated read-only `ora2pg_user` with `SELECT ANY DICTIONARY` + `SELECT_CATALOG_ROLE`. |
| One schema per Ora2Pg run | `SCHEMA HR` in config. A global run is an unbounded export that runs for hours. |
| Do **not** pre-create DDL in the target | Let Ora2Pg create the tables; pre-created tables cause constraint conflicts on `COPY`. |

---

## Character set

Oracle `WE8MSWIN1252` → PostgreSQL `UTF8`.

Set `NLS_LANG=AMERICAN_AMERICA.AL32UTF8` before running Ora2Pg. **Forgetting this corrupts French
accented characters** — and the corruption is silent until someone reads the data.

---

## Type mapping

Driven by two Ora2Pg settings that do most of the work:

| Setting | Value | Effect |
| --- | --- | --- |
| `PG_NUMERIC_TYPE` | `1` | Oracle `NUMBER` → smallest fitting PG numeric type |
| `PG_INTEGER_TYPE` | `1` | Oracle `NUMBER(N,0)` → `INTEGER` / `BIGINT` |

| Oracle | PostgreSQL | Note |
| --- | --- | --- |
| `NUMBER` (no precision) | `numeric` | Unbounded; prefer explicit precision at the source when you can |
| `NUMBER(N,0)` | `integer` / `bigint` | Chosen by magnitude when `PG_INTEGER_TYPE=1` |
| `NUMBER(p,s)` | `numeric(p,s)` | Scale preserved |
| `VARCHAR2(n)` | `varchar(n)` | Watch **byte vs char** semantics (`CHAR` vs `BYTE` length) |
| `CLOB` | `text` | |
| `BLOB` | `bytea` | Large objects can dominate export time — consider excluding and re-loading separately |
| `DATE` | `timestamp` | Oracle `DATE` carries a **time component** — mapping to PG `date` loses it |
| `TIMESTAMP WITH LOCAL TIME ZONE` | `timestamptz` | Verify the session time zone on both sides |
| `RAW(16)` | `uuid` or `bytea` | Only map to `uuid` when the column really holds one |

---

## SQL dialect differences that break at runtime

These pass schema conversion and fail later, so check them explicitly:

| Oracle | PostgreSQL | Note |
| --- | --- | --- |
| `SYSDATE` | `now()` / `current_timestamp` | |
| `NVL(a, b)` | `coalesce(a, b)` | |
| `DECODE(...)` | `CASE ... END` | |
| `ROWNUM <= n` | `LIMIT n` | Semantics differ when combined with `ORDER BY` |
| `dual` | (omit the FROM clause) | `SELECT 1` needs no table in PG |
| `||` concat with NULL | different NULL behaviour | Oracle treats `NULL` as empty string in concat; PG propagates NULL |
| Empty string `''` | **not** NULL in PG | Oracle equates `''` and `NULL`; PostgreSQL does not. This silently changes `IS NULL` predicates. |
| Sequences `seq.NEXTVAL` | `nextval('seq')` | Ora2Pg converts, but reset sequence values after data load |

> The empty-string / NULL divergence is the single most common source of post-migration
> behavioural bugs. It cannot be detected by row counts — only by application testing.

---

## PL/SQL → PL/pgSQL

Ora2Pg translates the structure and is honest about what it cannot convert — **review every
`FUNCTION`, `PROCEDURE` and `TRIGGER` output manually**.

Known conversion defect: Ora2Pg mishandles trailing slashes, rewriting
`END procedure_name;\n/` into `END procedure_name;\n;`, which PostgreSQL fails to parse.
Post-process the generated file before applying it.

Packages have no PostgreSQL equivalent — they become either schemas of standalone functions or an
application-side refactor. Budget for this in the assessment.

---

## Always start with the assessment

```
ora2pg -t SHOW_REPORT --estimate_cost -c ora2pg.conf
```

Skipping this is the number-one reason migrations derail mid-conversion: the complexity report is
what tells you whether packages, triggers and PL/SQL volume make the "simple" migration a multi-week
refactor.

---

## Related

- [`agents/03-oracle-to-postgres/oracle-to-postgres-migration-agent/`](agents/03-oracle-to-postgres/oracle-to-postgres-migration-agent/instructions.md) — CLI / Ora2Pg pipeline
- [`agents/03-oracle-to-postgres/oracle-to-postgres-copilot-modernization-agent/`](agents/03-oracle-to-postgres/oracle-to-postgres-copilot-modernization-agent/instructions.md) — GUI / Copilot path (also refactors app code)
- [`agents/03-oracle-to-postgres/oracle-source-vm-agent/`](agents/03-oracle-to-postgres/oracle-source-vm-agent/instructions.md) — Oracle XE source on Azure VM
- [migration_tooling.md](migration_tooling.md) — choosing between DMS / SSMA / DMA / Ora2Pg
