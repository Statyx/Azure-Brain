# Migration Tooling — Decision Matrix

Which tool for which cross-engine move. Pick the tool **before** writing any script — the choice
determines whether an online (near-zero-downtime) cutover is even possible.

---

## The two questions that decide everything

1. **Can the source produce a change stream?** (Oracle ARCHIVELOG + supplemental logging,
   SQL Server CDC, MySQL binlog, Mongo oplog.) No change stream → **offline cutover only**.
2. **Is the schema convertible automatically, or does it need refactoring?** Assessment output
   answers this — never assume.

---

## Matrix

| Source → Target | Tool | Online cutover | Notes |
| --- | --- | --- | --- |
| Oracle → PostgreSQL | **Ora2Pg** | ❌ offline (`COPY`) | Assessment + DDL/PL-SQL conversion + data export. The only path when the source is Oracle **XE**. |
| Oracle → PostgreSQL | **Azure DMS** | ✅ | Requires ARCHIVELOG + supplemental logging + LogMiner privileges. **Not available on Oracle XE.** |
| Oracle → PostgreSQL | **PG VS Code ext + Copilot App Mod** | ❌ offline | GUI/Copilot path; also refactors the **application** (e.g. Java → Managed Identity). |
| SQL Server → Azure SQL DB / MI | **DMA** then **DMS** | ✅ (DMS) | DMA = assessment + compatibility; DMS = the move. |
| SQL Server → Azure SQL | **SSMA** | ❌ | Mainly for heterogeneous sources into SQL; schema-conversion oriented. |
| MySQL → Azure DB for MySQL | **DMS** | ✅ | Binlog-based. |
| MongoDB → Cosmos DB (Mongo API/vCore) | **DMS** / native tooling | ✅ | Oplog-based for online. |
| PostgreSQL → Azure DB for PostgreSQL | **native logical replication** | ✅ | Simplest case — same engine, use publications/subscriptions. |

---

## Tool roles (don't confuse them)

| Tool | What it actually is |
| --- | --- |
| **DMA** (Data Migration Assistant) | Assessment + compatibility report. Does **not** move data at scale. |
| **SSMA** (SQL Server Migration Assistant) | Schema + code conversion **into** SQL Server / Azure SQL. |
| **Ora2Pg** | Assessment + DDL/PL-SQL conversion + bulk data export, Oracle → PostgreSQL. CLI, scriptable. |
| **Azure DMS** | Managed data movement service: initial load **+ CDC** for online cutovers. Not a schema-conversion tool. |

A common mistake is expecting DMS to convert a schema, or expecting Ora2Pg to give you a
near-zero-downtime cutover. They solve different halves of the problem — most real migrations use
one of each.

---

## Standard sequence

```
1. ASSESS       → complexity report, refactor backlog, go/no-go
2. CONVERT      → schema + procedural code, reviewed manually
3. LOAD         → initial data load into the target
4. REPLICATE    → CDC (only if the source supports a change stream)
5. VALIDATE     → row counts, checksums, application smoke tests
6. CUTOVER      → freeze, drain, switch connection strings, keep rollback ready
```

Never skip step 1, and never let step 5 be "the row counts match" — row counts do not catch the
dialect divergences (empty string vs NULL, DATE time components, NULL concat) that change
application behaviour. See [oracle_to_postgres.md](oracle_to_postgres.md).

---

## Related

- [oracle_to_postgres.md](oracle_to_postgres.md) — dialect and type reference for the live track
- [`agents/_catalog.yaml`](agents/_catalog.yaml) — agent roadmap and status
