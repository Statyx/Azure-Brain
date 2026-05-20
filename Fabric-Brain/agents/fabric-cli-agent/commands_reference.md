# Commands Reference — Fabric CLI (`fab`) Full Catalog

---

## Installation

```bash
pip install ms-fabric-cli        # install
pip install --upgrade ms-fabric-cli  # upgrade
fab --version                    # verify (v1.5.0+)
```

**Requires**: Python 3.10–3.13

---

## CLI Modes

| Mode | Behavior | Switch Command |
|------|----------|----------------|
| `command_line` (default) | Prefix every command with `fab` | `fab config set mode command_line` |
| `interactive` | Shell prompt `fab:/$`, no prefix needed | `fab config set mode interactive` |

---

## File System Commands (`fs`)

### Core Operations

| Command | Aliases | Purpose | Example |
|---------|---------|---------|---------|
| `ls` | `dir` | List workspaces/items/files | `fab ls ws.Workspace` |
| `mkdir` | `create` | Create workspace/item/directory | `fab mkdir ws.Workspace/lh.Lakehouse` |
| `cp` | `copy` | Copy item or file | `fab cp ./local.csv ws/lh.Lakehouse/Files/` |
| `mv` | `move` | Move item or file | `fab mv ws/old.Notebook ws/new.Notebook` |
| `rm` | `del` | Delete resource | `fab rm ws.Workspace/nb.Notebook` |
| `ln` | `mklink` | Create shortcut | `fab ln source ws/lh.Lakehouse/Tables/shortcut` |
| `cd` | — | Change directory (interactive mode) | `fab cd ws.Workspace` |
| `pwd` | — | Print working directory | `fab pwd` |

### Import/Export

| Command | Purpose | Example |
|---------|---------|---------|
| `import` | Import item definition (create or update) | `fab import ws.Workspace/nb.Notebook -i ./local/nb.Notebook` |
| `export` | Export item definition to disk | `fab export ws.Workspace/nb.Notebook -o /tmp` |
| `deploy` | Config-driven multi-item deployment | `fab deploy --config config.yml --target_env prod` |

### Properties & Metadata

| Command | Purpose | Example |
|---------|---------|---------|
| `get` | Get workspace/item properties | `fab get ws.Workspace/lh.Lakehouse` |
| `set` | Set property value | `fab set ws/nb.Notebook -q displayName -i "New Name"` |
| `exists` | Check if resource exists | `fab exists ws.Workspace/lh.Lakehouse` |
| `open` | Open resource in browser | `fab open ws.Workspace/rpt.Report` |
| `desc` | Describe/inspect resource | `fab desc ws.Workspace/lh.Lakehouse` |

### Resource Management

| Command | Purpose | Example |
|---------|---------|---------|
| `assign` | Assign resource to workspace | `fab assign cap.Capacity ws.Workspace` |
| `unassign` | Unassign resource | `fab unassign cap.Capacity ws.Workspace` |
| `start` | Start resource (legacy alias for job start) | `fab start ws/nb.Notebook` |
| `stop` | Stop resource | `fab stop ws/pool.SparkPool` |

---

## Listing with Filters

```bash
# Basic listing
fab ls                                            # all workspaces
fab ls ws.Workspace                               # items in workspace
fab ls ws.Workspace -l                            # detailed (long) listing
fab ls ws.Workspace/lh.Lakehouse/Files            # OneLake files
fab ls ws.Workspace/lh.Lakehouse/Tables           # Delta tables

# JMESPath filtering
fab ls ws.Workspace -q "[?contains(name,'Sales')]"       # name filter
fab ls ws.Workspace -q "[?type=='Notebook']"             # type filter
fab ls ws.Workspace -q "[?type=='Lakehouse'].name"       # project names only

# Output format
fab ls ws.Workspace --output_format json          # JSON output
fab ls ws.Workspace --output_format text          # text output (default)

# Show hidden/virtual items
fab config set show_hidden true
fab ls ws.Workspace                               # now shows .sparkpools, etc.
```

---

## Job Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `job run` | Run job synchronously (waits) | `fab job run ws/nb.Notebook --timeout 3600` |
| `job start` | Start job asynchronously | `fab job start ws/pl.DataPipeline` |
| `job run-sch` | Create scheduled run | `fab job run-sch ws/nb.Notebook --type daily --interval "09:00"` |
| `job run-list` | List job runs | `fab job run-list ws/nb.Notebook` |
| `job run-status` | Check run status | `fab job run-status ws/nb.Notebook --run-id <id>` |
| `job run-cancel` | Cancel a running job | `fab job run-cancel ws/nb.Notebook --run-id <id>` |
| `job run-update` | Update run parameters | `fab job run-update ws/nb.Notebook --run-id <id>` |
| `job run-rm` | Delete run record | `fab job run-rm ws/nb.Notebook --run-id <id>` |

### Job Parameters

```bash
# Pass parameters to pipeline/notebook
fab job run ws/pl.DataPipeline -P param1:string=value1 -P param2:int=42

# Schedule types
fab job run-sch ws/nb.Notebook --type daily --interval "09:00,15:00"
fab job run-sch ws/pl.DataPipeline --type weekly --interval "Monday,09:00"
```

---

## Table Commands (Delta)

| Command | Purpose | Example |
|---------|---------|---------|
| `table load` | Load data into Delta table | `fab table load Tables/sales --file data.csv` |
| `table schema` | Show table schema | `fab table schema Tables/employees` |
| `table optimize` | Optimize Delta table | `fab table optimize Tables/sales --vorder --zorder date,product_id` |
| `table vacuum` | Clean old Delta files | `fab table vacuum Tables/logs --retain_n_hours 24` |

### Table Load Options

```bash
# CSV load (default)
fab table load Tables/employees --file employees.csv

# Parquet load
fab table load Tables/sales --file data.parquet --format format=parquet

# Append mode (don't overwrite)
fab table load Tables/sales --file new_batch.csv --mode append

# Multiple files
fab table load Tables/sales --file data/ --format format=parquet --mode append
```

---

## OneLake File Operations

```bash
# Upload single file
fab cp ./local/data.csv ws.Workspace/lh.Lakehouse/Files/data.csv

# Upload directory
fab cp ./local/raw-data/ ws.Workspace/lh.Lakehouse/Files/raw-data/

# Download file
fab cp ws.Workspace/lh.Lakehouse/Files/report.csv ./local/

# Copy within OneLake
fab cp ws/lh.Lakehouse/Files/a.csv ws/lh.Lakehouse/Files/archive/a.csv

# Create directory
fab mkdir ws.Workspace/lh.Lakehouse/Files/raw-data/2024/

# Delete file
fab rm ws.Workspace/lh.Lakehouse/Files/old-data.csv

# List files
fab ls ws.Workspace/lh.Lakehouse/Files/raw-data/
```

---

## ACL Commands (Permissions)

```bash
# Add role to workspace
fab acl ws.Workspace -R Admin -i user@company.com

# List permissions
fab acl ws.Workspace -l

# Remove permission
fab acl ws.Workspace -R Admin -i user@company.com --remove
```

---

## Config Commands

```bash
fab config ls                          # list all settings
fab config get <setting>               # get value
fab config set <setting> <value>       # set value
```

### Key Settings

| Setting | Values | Purpose |
|---------|--------|---------|
| `mode` | `command_line`, `interactive` | CLI mode |
| `output_format` | `text`, `json` | Output format |
| `output_item_sort_criteria` | `byname`, `bytype` | Sorting |
| `show_hidden` | `true`, `false` | Show virtual items |
| `cache_enabled` | `true`, `false` | Enable caching |
| `debug_enabled` | `true`, `false` | Debug output |
| `folder_listing_enabled` | `true`, `false` | Show workspace folders |
| `default_capacity` | capacity name | Default capacity for new workspaces |
| `default_az_location` | region | Default Azure region |
| `default_az_subscription_id` | GUID | Default subscription |
| `default_open_experience` | `fabric`, `powerbi` | `fab open` target |
| `encryption_fallback_enabled` | `true`, `false` | Fix encrypted cache issues |

---

## API Command (Raw HTTP)

For operations not covered by built-in commands:

```bash
# GET request
fab api /v1/workspaces -X GET

# POST request with body
fab api /v1/workspaces/{wsId}/items -X POST -i '{"displayName":"test","type":"Notebook"}'

# With custom headers
fab api /v1/workspaces -X GET -H "Accept: application/json"
```

The `fab api` command uses the authenticated session — no manual token management needed.

---

## Key Parameters (Global)

| Short | Long | Purpose |
|-------|------|---------|
| `-a` | `--all` | Select/show all |
| `-f` | `--force` | Force operation, skip validation |
| `-h` | `--help` | Show help |
| `-i` | `--input` | JSON input path or inline content |
| `-l` | `--long` | Detailed listing output |
| `-o` | `--output` | Output file path |
| `-P` | `--params` | Parameters (key:type=value) |
| `-q` | `--query` | JMESPath filter expression |
| `-w` | `--wait` | Wait for job completion |
| `-R` | `--role` | ACL role (Admin, Member, Contributor, Viewer) |
| `-X` | `--method` | HTTP method for `api` command |
| `-H` | `--headers` | HTTP headers for `api` command |
| | `--output_format` | `text` or `json` |
| `-v` | `--verbose` | Verbose output |

---

## Item Type Suffixes

### Standard Item Types (30+)

| Suffix | Fabric Item |
|--------|-------------|
| `.Lakehouse` | Lakehouse |
| `.Warehouse` | Synapse Data Warehouse |
| `.SQLDatabase` | SQL Database |
| `.Notebook` | Spark Notebook |
| `.DataPipeline` | Data Pipeline |
| `.Report` | Power BI Report |
| `.SemanticModel` | Semantic Model |
| `.Dashboard` | Dashboard |
| `.Eventhouse` | Eventhouse |
| `.Eventstream` | Eventstream |
| `.KQLDatabase` | KQL Database |
| `.KQLDashboard` | KQL Dashboard |
| `.KQLQueryset` | KQL Queryset |
| `.Environment` | Spark Environment |
| `.SparkJobDefinition` | Spark Job Definition |
| `.MLExperiment` | ML Experiment |
| `.MLModel` | ML Model |
| `.CopyJob` | Copy Job |
| `.MirroredDatabase` | Mirrored Database |
| `.MirroredWarehouse` | Mirrored Warehouse |
| `.Datamart` | Datamart |
| `.Dataflow` | Dataflow Gen2 |
| `.PaginatedReport` | Paginated Report |
| `.GraphQLApi` | GraphQL API |
| `.GraphQuerySet` | Graph Query Set |
| `.MountedDataFactory` | Mounted Data Factory |
| `.VariableLibrary` | Variable Library |
| `.SQLEndpoint` | SQL Endpoint |
| `.Reflex` | Reflex |

### Virtual Item Types

| Suffix | Location | Purpose |
|--------|----------|---------|
| `.Workspace` | Tenant root | Workspace |
| `.Capacity` | `.capacities/` | Fabric capacity |
| `.Connection` | `.connections/` | Shared connection |
| `.Domain` | `.domains/` | Admin domain |
| `.Gateway` | `.gateways/` | Data gateway |
| `.SparkPool` | Workspace `.sparkpools/` | Spark pool |
| `.ManagedIdentity` | Workspace `.managedidentities/` | Managed identity |
