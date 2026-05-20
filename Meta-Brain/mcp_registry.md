# MCP Server Registry

Central catalog of all MCP servers available in the VS Code / Copilot environment.  
Each entry documents: purpose, tool prefix, key tools, and usage examples.

> **Rule**: Before calling any MCP tool, use `tool_search_tool_regex` to load it.  
> MCP tools are deferred — calling them without loading first will fail.

---

## Quick Reference

| Server | Prefix | Domain | Tools | Brain Doc |
|--------|--------|--------|-------|-----------|
| **Azure** | `mcp_azure_mcp_*` | Azure resource management | 50+ | — |
| **Fabric** | `mcp_fabric_mcp_*` | Fabric items, OneLake, tables | 20+ | — |
| **Power BI Model** | `mcp_powerbi-model_*` | Semantic model CRUD, DAX, TMDL | 21 | [`mcp_powerbi.md`](mcp_powerbi.md) |
| **Kusto** | `mcp_azure_mcp_kusto` | KQL queries, schema, clusters | 8 | [`agents/rti-kusto-agent/mcp_kusto.md`](agents/rti-kusto-agent/mcp_kusto.md) |
| **MCP Engine** | `mcp_mcp_engine_*` | Model management, dependencies | 15 | — |
| **GitKraken** | `mcp_gitkraken_*` | Git ops, issues, PRs | 20+ | — |
| **Pylance** | `mcp_pylance_*` | Python analysis, imports | 12 | — |

---

## 1. MCP Azure — Azure Resource Management

> **Prefix**: `mcp_azure_mcp_*`  
> **Source**: Built-in VS Code Azure extension  
> **Auth**: Azure CLI (`az login`)

The largest MCP server — covers nearly all Azure services. Each service has its own tool.

### Service Tools

| Tool | Azure Service | Key Actions |
|------|--------------|-------------|
| `mcp_azure_mcp_storage` | Storage Accounts | Blob, file shares, queues, tables |
| `mcp_azure_mcp_cosmos` | Cosmos DB | Database/container CRUD, queries |
| `mcp_azure_mcp_keyvault` | Key Vault | Secrets, keys, certificates |
| `mcp_azure_mcp_sql` | Azure SQL | Database management |
| `mcp_azure_mcp_postgres` | PostgreSQL | Flexible server management |
| `mcp_azure_mcp_mysql` | MySQL | Flexible server management |
| `mcp_azure_mcp_redis` | Redis Cache | Cache management |
| `mcp_azure_mcp_appservice` | App Service | Web app management |
| `mcp_azure_mcp_functionapp` | Functions | Function app management |
| `mcp_azure_mcp_aks` | AKS | Kubernetes cluster management |
| `mcp_azure_mcp_acr` | Container Registry | Image management |
| `mcp_azure_mcp_kusto` | Azure Data Explorer | KQL queries, schema — see [mcp_kusto.md](agents/rti-kusto-agent/mcp_kusto.md) |
| `mcp_azure_mcp_eventgrid` | Event Grid | Event subscriptions |
| `mcp_azure_mcp_eventhubs` | Event Hubs | Namespace/hub management |
| `mcp_azure_mcp_servicebus` | Service Bus | Queues, topics |
| `mcp_azure_mcp_signalr` | SignalR | Real-time messaging |
| `mcp_azure_mcp_search` | AI Search | Index/indexer management |
| `mcp_azure_mcp_foundry` | AI Foundry | Model deployment |
| `mcp_azure_mcp_speech` | Speech Services | Speech-to-text, text-to-speech |
| `mcp_azure_mcp_applicationinsights` | Application Insights | Telemetry queries |
| `mcp_azure_mcp_monitor` | Azure Monitor | Metrics, alerts, logs |
| `mcp_azure_mcp_loadtesting` | Load Testing | Performance tests |
| `mcp_azure_mcp_grafana` | Managed Grafana | Dashboard management |

### Management Tools

| Tool | Purpose |
|------|---------|
| `mcp_azure_mcp_subscription_list` | List Azure subscriptions |
| `mcp_azure_mcp_group_list` | List resource groups |
| `mcp_azure_mcp_role` | RBAC role assignments |
| `mcp_azure_mcp_quota` | Check quotas and limits |
| `mcp_azure_mcp_resourcehealth` | Resource health status |
| `mcp_azure_mcp_deploy` | ARM/Bicep deployments |
| `mcp_azure_mcp_documentation` | Azure docs lookup |
| `mcp_azure_mcp_get_bestpractices` | Best practices for a service |
| `mcp_azure_mcp_marketplace` | Marketplace offerings |

### Specialized Tools

| Tool | Purpose |
|------|---------|
| `mcp_azure_mcp_appconfig` | App Configuration |
| `mcp_azure_mcp_applens` | AppLens diagnostics |
| `mcp_azure_mcp_azd` | Azure Developer CLI (azd) |
| `mcp_azure_mcp_bicepschema` | Bicep schema reference |
| `mcp_azure_mcp_cloudarchitect` | Architecture recommendations |
| `mcp_azure_mcp_communication` | Communication Services |
| `mcp_azure_mcp_confidentialledger` | Confidential Ledger |
| `mcp_azure_mcp_datadog` | Datadog integration |
| `mcp_azure_mcp_managedlustre` | Managed Lustre |
| `mcp_azure_mcp_virtualdesktop` | Azure Virtual Desktop |
| `mcp_azure_mcp_workbooks` | Azure Workbooks |
| `mcp_azure_mcp_azureterraformbestpractices` | Terraform best practices |

### CLI Extension Tools

| Tool | Purpose |
|------|---------|
| `mcp_azure_mcp_extension_azqr` | Azure Quick Review (compliance) |
| `mcp_azure_mcp_extension_cli_generate` | Generate CLI commands |
| `mcp_azure_mcp_extension_cli_install` | Install CLI extensions |

### Usage Example

```
# List storage accounts in a resource group
mcp_azure_mcp_storage(
    action: "list",
    resourceGroup: "rg-my-project",
    subscription: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
)
```

---

## 2. MCP Fabric — Fabric Items & OneLake

> **Prefix**: `mcp_fabric_mcp_*`  
> **Source**: Fabric MCP extension  
> **Auth**: Azure CLI (`az login`) or Fabric token

Direct access to Fabric workspace items and OneLake file/table storage. Bypasses REST API boilerplate.

### Core Tools

| Tool | Purpose |
|------|---------|
| `mcp_fabric_mcp_core_create-item` | Create any Fabric item (notebook, lakehouse, etc.) |

### OneLake File Operations

| Tool | Purpose |
|------|---------|
| `mcp_fabric_mcp_onelake_list_workspaces` | List all Fabric workspaces |
| `mcp_fabric_mcp_onelake_list_items` | List items in a workspace |
| `mcp_fabric_mcp_onelake_list_items_dfs` | List items via DFS endpoint |
| `mcp_fabric_mcp_onelake_list_files` | List files in a lakehouse/item |
| `mcp_fabric_mcp_onelake_upload_file` | Upload file to OneLake |
| `mcp_fabric_mcp_onelake_download_file` | Download file from OneLake |
| `mcp_fabric_mcp_onelake_delete_file` | Delete file from OneLake |
| `mcp_fabric_mcp_onelake_create_directory` | Create directory in OneLake |
| `mcp_fabric_mcp_onelake_delete_directory` | Delete directory from OneLake |

### OneLake Table Operations

| Tool | Purpose |
|------|---------|
| `mcp_fabric_mcp_onelake_list_tables` | List Delta tables in a lakehouse |
| `mcp_fabric_mcp_onelake_get_table` | Read table data (Delta format) |
| `mcp_fabric_mcp_onelake_get_table_config` | Get table configuration |
| `mcp_fabric_mcp_onelake_list_table_namespaces` | List table namespaces |
| `mcp_fabric_mcp_onelake_get_table_namespace` | Get table namespace details |

### Documentation Tools

| Tool | Purpose |
|------|---------|
| `mcp_fabric_mcp_docs_best-practices` | Fabric best practices |
| `mcp_fabric_mcp_docs_item-definitions` | Item definition formats |
| `mcp_fabric_mcp_docs_platform-api-spec` | Platform API spec |
| `mcp_fabric_mcp_docs_workload-api-spec` | Workload API spec |
| `mcp_fabric_mcp_docs_workloads` | Workload documentation |
| `mcp_fabric_mcp_docs_api-examples` | API usage examples |

### Usage Examples

```
# List workspaces
mcp_fabric_mcp_onelake_list_workspaces()

# List files in a lakehouse
mcp_fabric_mcp_onelake_list_files(
    workspace: "CDR - Fabric RTI Demo",
    item: "LH_SensorReference",
    path: "Files/"
)

# Read a Delta table
mcp_fabric_mcp_onelake_get_table(
    workspace: "CDR - Fabric RTI Demo",
    item: "LH_SensorReference",
    table: "dim_sensors"
)

# Upload a CSV
mcp_fabric_mcp_onelake_upload_file(
    workspace: "CDR - Fabric RTI Demo",
    item: "LH_SensorReference",
    path: "Files/new_data.csv",
    localPath: "data/raw/new_data.csv"
)
```

### When to Use MCP Fabric vs REST API

| Scenario | Use |
|----------|-----|
| Quick file listing / read | **MCP Fabric** — zero boilerplate |
| Read Delta table contents | **MCP Fabric** `get_table` |
| Create/update notebook definition | **REST API** (MCP only has `create-item`) |
| Run notebook via Jobs API | **REST API** (no MCP equivalent) |
| Upload small files (<100MB) | **MCP Fabric** `upload_file` |
| Complex multi-step deployments | **REST API** with `notebook_utils.py` |

---

## 3. MCP Power BI Model — Semantic Model CRUD

> **Prefix**: `mcp_powerbi-model_*`  
> **Source**: [powerbi-modeling-mcp](https://github.com/microsoft/powerbi-modeling-mcp)  
> **Auth**: Fabric XML/A endpoint or Power BI Desktop local  
> **Full reference**: [`mcp_powerbi.md`](mcp_powerbi.md)

21 tools for complete semantic model management. The most powerful MCP server for data modeling.

### Tool Categories

| Category | Tools | Key Operations |
|----------|-------|----------------|
| **Connection** | `connection_operations` | ConnectFabric, Connect, Disconnect, ListLocalInstances |
| **Modeling** | `table_operations`, `column_operations`, `measure_operations`, `relationship_operations`, `model_operations` | CRUD, descriptions, summarizeBy, isHidden |
| **Advanced** | `calculation_group_operations`, `calendar_operations`, `partition_operations`, `perspective_operations`, `user_hierarchy_operations` | Calc groups, time intelligence, partitions |
| **Queries** | `dax_query_operations`, `trace_operations`, `transaction_operations` | Execute/validate DAX, profiling |
| **Deploy** | `database_operations`, `culture_operations`, `object_translation_operations`, `named_expression_operations`, `function_operations`, `query_group_operations`, `security_role_operations` | TMDL export/import, deploy, RLS |

### Quick Start

```
# 1. Connect to Fabric semantic model
mcp_powerbi-model_connection_operations(operation: "ConnectFabric", workspaceName: "My Workspace", semanticModelName: "My Model")

# 2. List all measures
mcp_powerbi-model_measure_operations(operation: "List")

# 3. Add a measure
mcp_powerbi-model_measure_operations(operation: "Create", definitions: [{name: "Revenue YTD", tableName: "Sales", expression: "TOTALYTD([Revenue], 'Calendar'[Date])"}])

# 4. Execute DAX
mcp_powerbi-model_dax_query_operations(operation: "Execute", query: "EVALUATE ROW(\"Test\", [Revenue YTD])")
```

---

## 4. MCP Kusto — KQL Queries & Schema

> **Prefix**: `mcp_azure_mcp_kusto`  
> **Part of**: MCP Azure server  
> **Auth**: Azure CLI  
> **Full reference**: [`agents/rti-kusto-agent/mcp_kusto.md`](agents/rti-kusto-agent/mcp_kusto.md)

8 tools for read-only Kusto/Eventhouse access. Works with both Azure Data Explorer and Fabric Eventhouse.

### Tools

| Tool | Purpose |
|------|---------|
| `kusto_query` | Run any KQL query |
| `kusto_sample` | Quick table preview |
| `kusto_cluster_list` | List clusters in subscription |
| `kusto_cluster_get` | Cluster details |
| `kusto_database_list` | List databases |
| `kusto_table_list` | List tables |
| `kusto_table_schema` | Column names, types |
| `kusto_function_list` | Stored functions |

### Quick Start

```
# Query an Eventhouse
mcp_azure_mcp_kusto(
    tool: "kusto_query",
    database: "EH_SensorTelemetry",
    query: "SensorReading | summarize count() by SensorType | order by count_ desc",
    cluster-uri: "https://trd-xyz.z9.kusto.fabric.microsoft.com"
)
```

---

## 5. MCP Engine — Model Management

> **Prefix**: `mcp_mcp_engine_*`  
> **Source**: MCP Engine extension

Manages data models, dependencies, schemas, and policies. Useful for enterprise model governance.

### Tools

| Tool | Purpose |
|------|---------|
| `mcp_mcp_engine_list_model` | List available models |
| `mcp_mcp_engine_manage_dependencies` | Model dependency tracking |
| `mcp_mcp_engine_manage_license` | License management |
| `mcp_mcp_engine_manage_localization` | Localization settings |
| `mcp_mcp_engine_manage_memory` | Memory configuration |
| `mcp_mcp_engine_manage_model_changes` | Track model changes |
| `mcp_mcp_engine_manage_model_connection` | Connection management |
| `mcp_mcp_engine_manage_model_properties` | Model properties |
| `mcp_mcp_engine_manage_policy` | Policy management |
| `mcp_mcp_engine_manage_schema` | Schema operations |
| `mcp_mcp_engine_manage_security` | Security configuration |
| `mcp_mcp_engine_manage_semantic` | Semantic layer management |
| `mcp_mcp_engine_manage_tests` | Test management |
| `mcp_mcp_engine_refresh` | Refresh operations |
| `mcp_mcp_engine_run_query` | Execute queries |

---

## 6. MCP GitKraken — Git & Issues

> **Prefix**: `mcp_gitkraken_*`  
> **Source**: GitKraken / GitLens extension

Full Git operations plus issue/PR management without leaving the editor.

### Git Operations

| Tool | Purpose |
|------|---------|
| `mcp_gitkraken_git_status` | Working tree status |
| `mcp_gitkraken_git_add_or_commit` | Stage and commit |
| `mcp_gitkraken_git_push` | Push to remote |
| `mcp_gitkraken_git_branch` | Branch management |
| `mcp_gitkraken_git_checkout` | Switch branches |
| `mcp_gitkraken_git_log_or_diff` | History and diffs |
| `mcp_gitkraken_git_blame` | Line-by-line blame |
| `mcp_gitkraken_git_stash` | Stash changes |
| `mcp_gitkraken_git_worktree` | Worktree management |

### Issues & PRs

| Tool | Purpose |
|------|---------|
| `mcp_gitkraken_issues_assigned_to_me` | My assigned issues |
| `mcp_gitkraken_issues_get_detail` | Issue details |
| `mcp_gitkraken_issues_add_comment` | Comment on issue |
| `mcp_gitkraken_pull_request_assigned_to_me` | My PRs |
| `mcp_gitkraken_pull_request_get_detail` | PR details |
| `mcp_gitkraken_pull_request_get_comments` | PR comments |
| `mcp_gitkraken_pull_request_create` | Create PR |
| `mcp_gitkraken_pull_request_create_review` | Submit review |

### GitLens Features

| Tool | Purpose |
|------|---------|
| `mcp_gitkraken_gitlens_launchpad` | GitLens Launchpad |
| `mcp_gitkraken_gitlens_start_work` | Start working on issue |
| `mcp_gitkraken_gitlens_start_review` | Start code review |
| `mcp_gitkraken_gitlens_commit_composer` | Compose commit message |

---

## 7. MCP Pylance — Python Analysis

> **Prefix**: `mcp_pylance_*`  
> **Source**: Pylance extension

Python-specific code intelligence — useful for refactoring, imports, and environment management.

### Tools

| Tool | Purpose |
|------|---------|
| `mcp_pylance_mcp_s_pylanceDocString` | Generate docstrings |
| `mcp_pylance_mcp_s_pylanceDocuments` | Document analysis |
| `mcp_pylance_mcp_s_pylanceFileSyntaxErrors` | File syntax errors |
| `mcp_pylance_mcp_s_pylanceSyntaxErrors` | All syntax errors |
| `mcp_pylance_mcp_s_pylanceImports` | Import analysis |
| `mcp_pylance_mcp_s_pylanceInstalledTopLevelModules` | Installed packages |
| `mcp_pylance_mcp_s_pylanceInvokeRefactoring` | Run refactorings |
| `mcp_pylance_mcp_s_pylancePythonEnvironments` | List Python envs |
| `mcp_pylance_mcp_s_pylanceUpdatePythonEnvironment` | Switch env |
| `mcp_pylance_mcp_s_pylanceRunCodeSnippet` | Execute snippet |
| `mcp_pylance_mcp_s_pylanceSettings` | Pylance settings |
| `mcp_pylance_mcp_s_pylanceWorkspaceRoots` | Workspace roots |
| `mcp_pylance_mcp_s_pylanceWorkspaceUserFiles` | User files |

---

## Decision Guide — Which MCP Server to Use?

| I want to... | Use |
|--------------|-----|
| Query an Eventhouse / KQL database | **MCP Kusto** (`kusto_query`) |
| Read a Delta table from a Lakehouse | **MCP Fabric** (`get_table`) |
| Upload files to OneLake | **MCP Fabric** (`upload_file`) |
| Add descriptions to a semantic model | **MCP Power BI** (`column_operations`, `table_operations`) |
| Create DAX measures | **MCP Power BI** (`measure_operations`) |
| Run a DAX query | **MCP Power BI** (`dax_query_operations`) |
| Deploy TMDL to Fabric | **MCP Power BI** (`database_operations`) |
| Check Azure storage accounts | **MCP Azure** (`mcp_azure_mcp_storage`) |
| Manage Key Vault secrets | **MCP Azure** (`mcp_azure_mcp_keyvault`) |
| Create a git commit | **MCP GitKraken** (`git_add_or_commit`) |
| Analyze Python imports | **MCP Pylance** (`pylanceImports`) |
| List Fabric workspaces | **MCP Fabric** (`list_workspaces`) |
| Check Azure resource health | **MCP Azure** (`mcp_azure_mcp_resourcehealth`) |
| Run a notebook in Fabric | **REST API** (no MCP tool for this) |
| Create a Fabric pipeline | **REST API** (no MCP tool for this) |
