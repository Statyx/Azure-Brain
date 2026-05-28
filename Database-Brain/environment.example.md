# Database-Brain Environment — TEMPLATE
# Copy to environment.md (gitignored) and fill with your local values.

local_paths:
  workspace_root: "C:\\Users\\<USER>\\path\\to\\Azure-Brain"
  database_brain_root: "C:\\Users\\<USER>\\path\\to\\Azure-Brain\\Database-Brain"

azure_cli:
  default_subscription_alias: "<your subscription name>"
  default_location: "westeurope"

migration_tooling_installs:
  ora2pg: "C:\\Tools\\ora2pg"          # if doing Oracle to Postgres
  ssma: "C:\\Tools\\SSMA for Oracle"   # if doing SQL Server migration assessments
  azure_dms_cli: "az dms"              # via Azure CLI extension
