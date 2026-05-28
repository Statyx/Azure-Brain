# postgres-deploy-agent

## Role

Deploy **Azure Database for PostgreSQL — Flexible Server** as the **target** for Oracle migration
demos (or any greenfield PG workload).

Default profile: demo-ready, secure-by-default, single AZ. HA / read replicas added on demand.

## Scope

| In scope | Out of scope |
|---|---|
| Flexible Server (Burstable / GP / Memory Optimized) | Single Server (deprecated) |
| Networking: VNet integration OR public + firewall (operator IP) | Private Link to multi-region peering |
| Entra ID admin + Postgres admin | Custom row-level security policies |
| Server parameters tuned for migration (logical replication, max_wal_senders, max_connections) | Per-app schema design |
| Extensions allow-list (`uuid-ossp`, `pgcrypto`, `pg_trgm`, `pgvector`, `orafce`) | Custom C extensions |
| HA: ZoneRedundant in supported regions (parametrised) | Cross-region read replicas |

## Hard rules

1. **Flexible Server only**. Single Server is deprecated (March 2025 retirement).
2. **PostgreSQL 16** by default. Versions 11–13 forbidden (out of support).
3. **Tier defaults**: demo = `Standard_B2ms` (Burstable 2 vCPU / 8 GB), prod = `Standard_D4ds_v5` (GP).
4. **Storage**: 128 GB minimum, **auto-grow ENABLED** always. Bumping IOPS without bumping storage is a frequent foot-gun.
5. **Backup retention**: 7 days minimum (default 7, max 35). Geo-redundant backup ON for prod.
6. **TLS**: enforce `require_secure_transport = ON` always.
7. **Admin auth**: Entra-only when feasible (`createMode = Default` + AD admin). Password admin kept ONLY for migration tooling that doesn't support Entra (Ora2Pg, DMS use password).
8. **Logical replication**: enable `wal_level=logical` + `max_wal_senders=10` from day 1 when this server is a DMS target — changing it later forces restart.
9. **Extensions**: enable via `azure.extensions` server parameter (comma-separated, lowercase). Never `CREATE EXTENSION` before enabling at server level — fails with "extension not allowed".
10. **NSG / firewall**: when public access mode, allow ONLY operator IP. For VNet integration, no public endpoint.

## Inputs

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `serverName` | string | — | Globally unique, lowercase, 3-63 chars |
| `location` | string | `francecentral` | |
| `pgVersion` | string | `16` | `13`, `14`, `15`, `16` |
| `tier` | string | `Burstable` | `Burstable`, `GeneralPurpose`, `MemoryOptimized` |
| `skuName` | string | `Standard_B2ms` | Must match tier |
| `storageSizeGb` | int | `128` | Min 32, max 32768 |
| `storageAutogrow` | bool | `true` | |
| `adminUser` | string | `pgadmin` | Postgres native admin (used by migration tools) |
| `adminPasswordSecretUri` | string | — | Key Vault secret URI |
| `entraAdminObjectId` | string | — | Entra principal granted PG admin |
| `entraAdminPrincipalName` | string | — | UPN or app name |
| `enablePublicAccess` | bool | `false` | If true, must provide allowedSourceIp |
| `allowedSourceIp` | string | `''` | Required when public access |
| `vnetSubnetId` | string | `''` | Required when private access (VNet delegation) |
| `enableLogicalReplication` | bool | `true` | Required for DMS target |
| `enabledExtensions` | array | `[ 'uuid-ossp', 'pgcrypto', 'pg_trgm', 'orafce' ]` | `orafce` provides Oracle compat functions |
| `haMode` | string | `Disabled` | `Disabled`, `ZoneRedundant`, `SameZone` |

## Files in this agent folder

- [instructions.md](instructions.md) — this file
- [postgres-flex.bicep](postgres-flex.bicep) — main template
- [scripts/post-deploy.sh](scripts/post-deploy.sh) — psql commands: CREATE EXTENSION, create migration schema, grants
- [README.md](README.md) — quickstart

## Server parameters set automatically

| Parameter | Value | Reason |
|---|---|---|
| `azure.extensions` | from `enabledExtensions` param | Whitelist before `CREATE EXTENSION` |
| `wal_level` | `logical` (if `enableLogicalReplication`) | DMS source/target requirement |
| `max_wal_senders` | `10` | DMS + future read replicas |
| `max_replication_slots` | `10` | DMS slot |
| `require_secure_transport` | `ON` | TLS-only |
| `log_statement` | `ddl` (demo) / `none` (prod) | Audit during demo |

## Validation checklist

- [ ] `psql "host=<fqdn> dbname=postgres user=<admin> sslmode=require"` connects
- [ ] `SHOW wal_level;` returns `logical`
- [ ] `SELECT * FROM pg_available_extensions WHERE name = 'orafce';` returns row
- [ ] Entra admin can connect with `az account get-access-token` token

## Related agents

- [oracle-source-vm-agent](../../03-oracle-to-postgres/oracle-source-vm-agent/instructions.md) — source environment
- [oracle-to-postgres-migration-agent](../../03-oracle-to-postgres/oracle-to-postgres-migration-agent/instructions.md) — orchestrates Ora2Pg + DMS pointing here
