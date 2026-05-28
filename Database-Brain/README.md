# Database-Brain

**Azure database agents + knowledge files for designing, deploying, migrating and operating Azure database workloads with GitHub Copilot — zero re-learning, zero repeated mistakes.**

> Part of the [**Azure-Brain**](../README.md) umbrella. For cross-cutting agents (testing, PPTX, architecture diagrams) see [`../Meta-Brain/`](../Meta-Brain/README.md).

![Status](https://img.shields.io/badge/status-active-brightgreen?style=for-the-badge)
![Brain](https://img.shields.io/badge/brain-Database-blue?style=for-the-badge&logo=azuredatastudio)
![Scope](https://img.shields.io/badge/scope-OLTP_%7C_NoSQL_%7C_Migration-orange?style=for-the-badge)
![Agents](https://img.shields.io/badge/agents-4_active_%2F_18_total-blue?style=for-the-badge)

---

## Scope

Database-Brain covers the **operational data plane** on Azure — every project where the unit of work is a database (not a lakehouse, not a warehouse, not a semantic model — those live in `Fabric-Brain`).

Target scenarios:

| Scenario | Examples |
| --- | --- |
| **Greenfield deployment** | Azure SQL Database, Azure SQL Managed Instance, PostgreSQL Flexible Server, MySQL Flexible Server, Cosmos DB (NoSQL / Mongo / Cassandra / Gremlin / Table) |
| **Cross-engine migration** | Oracle → PostgreSQL, Oracle → Azure SQL, SQL Server → Azure SQL MI, MongoDB → Cosmos DB, DB2 → PostgreSQL |
| **Lift & shift** | SQL Server VM → Azure SQL MI, on-prem PG → Flexible Server, on-prem Mongo → Cosmos DB for MongoDB vCore |
| **Modernization** | Schema refactor, partitioning, performance tuning, HA/DR design, security hardening, vector / AI workloads on PG (pgvector) and Cosmos DB (DiskANN) |
| **Operations** | Backup / PITR, geo-replication, failover groups, monitoring, cost optimization, capacity planning |

---

## Active & Planned Agents

> See [`agents/_catalog.yaml`](agents/_catalog.yaml) for the source of truth. Status legend: 🟢 active (implemented) · 🟡 planned · ⚫ deprecated.

### Domain 01 — Relational (Azure SQL family)
- 🟡 `azuresql-deploy-agent` — Azure SQL DB / MI deployment, networking, security, HA/DR
- 🟡 `azuresql-tuning-agent` — query store, missing indexes, intelligent performance, automatic tuning
- 🟡 `azuresql-migration-agent` — SSMA, DMS, DMA, schema conversion, cutover playbook

### Domain 02 — PostgreSQL
- 🟢 [`postgres-deploy-agent`](agents/02-postgres/postgres-deploy-agent/instructions.md) — Flexible Server deployment (Bicep), extensions allow-list, logical replication for migration targets
- 🟡 `postgres-tuning-agent` — pg_stat_statements, autovacuum, query plans, partitioning
- 🟡 `postgres-pgvector-agent` — pgvector / DiskANN for AI workloads, embedding pipelines

### Domain 03 — Oracle source + Oracle→PostgreSQL Migration
- 🟢 [`oracle-source-vm-agent`](agents/03-oracle-to-postgres/oracle-source-vm-agent/instructions.md) — Oracle 21c XE on Azure VM (Bicep + cloud-init), sample schemas HR/SH/OE
- 🟢 [`oracle-to-postgres-migration-agent`](agents/03-oracle-to-postgres/oracle-to-postgres-migration-agent/instructions.md) — end-to-end Ora2Pg pipeline (assessment → schema → data → validate). **CLI / scriptable path**
- 🟢 [`oracle-to-postgres-copilot-modernization-agent`](agents/03-oracle-to-postgres/oracle-to-postgres-copilot-modernization-agent/instructions.md) — **PostgreSQL VS Code extension + GitHub Copilot App Modernization for Java** (official Microsoft 2026 toolchain). **GUI / Copilot path**, refactors DB + Java app code in one workflow with Managed Identity
- ⚫ `ora2pg-assessment-agent`, `ora2pg-schema-agent`, `ora2pg-cutover-agent` — superseded by the consolidated migration agent above

### Domain 04 — Cosmos DB
- 🟡 `cosmos-design-agent` — partition key design, RU/s sizing, consistency model, indexing policy
- 🟡 `cosmos-multi-api-agent` — NoSQL / Mongo / Cassandra / Gremlin / Table choice + idioms
- 🟡 `cosmos-vector-agent` — vector search (DiskANN), AI agent state store, change feed
- 🟡 `cosmos-cost-agent` — autoscale vs provisioned, RU optimization, serverless trade-offs

### Domain 05 — MySQL & MariaDB
- 🟡 `mysql-deploy-agent` — Flexible Server, HA, read replicas, networking
- 🟡 `mysql-migration-agent` — on-prem / AWS RDS → Azure DB for MySQL

### Domain 06 — Cross-Engine & Operations
- 🟡 `database-migration-orchestrator-agent` — picks the right tool (DMS, SSMA, Ora2Pg, MongoShake), runs the wave plan
- 🟡 `database-security-agent` — Entra-only auth, private endpoints, TDE, customer-managed keys, audit, Defender for SQL
- 🟡 `database-monitoring-agent` — Azure Monitor, Query Performance Insight, log analytics workbooks
- 🟡 `database-backup-dr-agent` — PITR, geo-redundant backup, failover groups, BCDR runbook

---

## Knowledge Files (planned)

| File | Purpose |
| --- | --- |
| `azuresql_essentials.md` | Tiers (DTU vs vCore vs Hyperscale), networking, auth, HA/DR |
| `postgres_essentials.md` | Flexible Server tiers, HA modes, extensions allow-list, version policy |
| `cosmos_essentials.md` | Partition key, RU/s, consistency, multi-region, change feed |
| `oracle_to_postgres.md` | Ora2Pg workflow, PL/SQL → PL/pgSQL patterns, DMS Oracle source config |
| `migration_tooling.md` | DMS vs SSMA vs DMA vs Ora2Pg vs MongoShake — decision matrix |
| `database_security.md` | Entra-only auth, private endpoints, TDE/CMK, network isolation |
| `database_cost.md` | Sizing methodology, reserved capacity vs autoscale, dev/test discounts |
| `vector_workloads.md` | pgvector vs Cosmos DB DiskANN vs AI Search — when to use which |

---

## Status

� **Active** — 3 agents implemented end-to-end for the **Oracle→PostgreSQL demo track**: Oracle source VM, PostgreSQL target, and the Ora2Pg migration pipeline. Other domains remain planned and are added on demand.

Demo workflow — pick the path based on audience:

**Common foundation (steps 1-2):**
1. Deploy Oracle XE source: [`oracle-source-vm-agent`](agents/03-oracle-to-postgres/oracle-source-vm-agent/README.md)
2. Deploy PostgreSQL target: [`postgres-deploy-agent`](agents/02-postgres/postgres-deploy-agent/README.md)

**Then pick ONE migration path (or combine for grand-compte demo):**

| Path | Tool | Audience | Effort | Output |
| --- | --- | --- | --- | --- |
| **A — CLI** | [`oracle-to-postgres-migration-agent`](agents/03-oracle-to-postgres/oracle-to-postgres-migration-agent/README.md) (Ora2Pg) | DBAs, data engineers | 30 min | DB only |
| **B — GUI/Copilot** ⭐ | [`oracle-to-postgres-copilot-modernization-agent`](agents/03-oracle-to-postgres/oracle-to-postgres-copilot-modernization-agent/README.md) (PG VS Code ext + Copilot App Mod Java) | Cloud architects, devs, decision-makers | 45 min | DB **+ Java app refactored to Managed Identity** |
| **C — Combo** | A for data, B for code | Grand-compte full-stack pitch | 1 h | Killer demo |

When adding the next agent:
1. Create folder `agents/{domain}/{agent-name}/` with `instructions.md` + `README.md`
2. Flip status to `active` in [`agents/_catalog.yaml`](agents/_catalog.yaml)
3. Update the agent list above
4. Update `Meta-Brain/tests/test_smoke.py` `BRAINS = [...]` constant to include `"Database-Brain"` (if not already done)
5. Run umbrella tests from `Meta-Brain/`:
   ```bash
   cd ../Meta-Brain
   python -m pytest tests/ -v --tb=short
   ```

---

## Setup

Like the other brains, sensitive config lives in `.gitignore`'d files:

```bash
cp resource_ids.example.md resource_ids.md    # fill with subscription / RG / server IDs
cp environment.example.md environment.md      # fill with local paths
```

See [`../GETTING_STARTED.md`](../GETTING_STARTED.md) for the umbrella setup guide.

---

## Cross-brain references

- [`../agent_principles.md`](../agent_principles.md) — mandatory operating principles every agent follows
- [`../shared_constraints.md`](../shared_constraints.md) — 8 hard rules across all brains
- [`../known_issues.md`](../known_issues.md) — cross-cutting gotchas
- [`../ERROR_RECOVERY.md`](../ERROR_RECOVERY.md) — decision trees by HTTP status
