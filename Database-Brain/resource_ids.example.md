# Database-Brain Resource IDs — TEMPLATE
# Copy to resource_ids.md (gitignored) and fill with your actual Azure resource IDs.
# NEVER commit resource_ids.md — it contains subscription / tenant / server IDs (OSINT risk).

# ──────────────────────────────────────────────
# Subscription & tenant
# ──────────────────────────────────────────────
subscription_id: "<your-subscription-guid>"
tenant_id: "<your-tenant-guid>"
default_resource_group: "<rg-name>"
default_location: "westeurope"

# ──────────────────────────────────────────────
# Azure SQL
# ──────────────────────────────────────────────
azuresql:
  server_name: "<server-name>"        # without .database.windows.net
  database_name: "<db-name>"
  admin_user: "<entra-group-or-user>"

# ──────────────────────────────────────────────
# PostgreSQL Flexible Server
# ──────────────────────────────────────────────
postgres:
  server_name: "<pg-flex-name>"       # without .postgres.database.azure.com
  database_name: "<db-name>"
  admin_user: "<entra-group-or-user>"

# ──────────────────────────────────────────────
# Cosmos DB
# ──────────────────────────────────────────────
cosmos:
  account_name: "<cosmos-account>"
  api: "<sql | mongo | cassandra | gremlin | table>"
  database_name: "<db-name>"
  primary_region: "westeurope"

# ──────────────────────────────────────────────
# Migration source (Oracle / SQL Server / Mongo etc.)
# ──────────────────────────────────────────────
migration_source:
  type: "<oracle | sqlserver | mongodb | mysql>"
  host: "<host-or-vnet-reachable-endpoint>"
  port: 1521
  service_or_database: "<service-name-or-db>"
