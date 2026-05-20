# CI/CD & Deployment Patterns — Fabric CLI

---

## Overview

The Fabric CLI `deploy` command provides config-driven, multi-item deployment across environments. It complements `import`/`export` for single-item operations.

### When to Use What

| Scenario | Command |
|----------|---------|
| Single item → Fabric | `fab import` |
| Single item ← Fabric | `fab export` |
| Multi-item, multi-env deployment | `fab deploy --config config.yml` |
| One-off pipeline trigger | `fab job run` / `fab job start` |

---

## Deploy Config YAML

### Minimal Config

```yaml
core:
  workspace_id: "12345678-1234-1234-1234-123456789abc"
  repository_directory: "."
```

This publishes **all** item types from the current directory into the specified workspace.

### Full Config with Environments

```yaml
core:
  workspace_id:
    dev: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    test: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    prod: "cccccccc-cccc-cccc-cccc-cccccccccccc"
  repository_directory: "."
  item_types_in_scope: [Notebook, DataPipeline, Lakehouse]
  parameter: params.yml

publish:
  exclude_regex: "^DONT_DEPLOY.*"
  skip:
    dev: false
    test: false
    prod: false

unpublish:
  exclude_regex: "^DEBUG.*"
  skip:
    dev: true
    test: true
    prod: false
```

### Config Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `core.workspace_id` | **Yes** | Target workspace GUID. String for single env, map for multi-env |
| `core.repository_directory` | **Yes** | Relative path to item definitions on disk |
| `core.item_types_in_scope` | No | Filter which item types to deploy (default: all) |
| `core.parameter` | No | Path to parameter file for find/replace |
| `publish.exclude_regex` | No | Regex pattern — matching items skip publishing |
| `publish.skip.<env>` | No | Skip publishing entirely for this env (`true`/`false`) |
| `unpublish.exclude_regex` | No | Regex pattern — matching items skip unpublishing |
| `unpublish.skip.<env>` | No | Skip unpublishing for this env (`true`/`false`) |

---

## Parameter Files (Find/Replace)

Parameter files enable environment-specific substitution in item definitions during deployment.

### Basic Parameter File (`params.yml`)

```yaml
find_replace:
  - find_value: "dev-connection-string"
    replace_value:
      dev: "dev-connection-string"
      test: "test-connection-string"
      prod: "prod-connection-string"

  - find_value: "dev-lakehouse-id"
    replace_value:
      dev: "11111111-1111-1111-1111-111111111111"
      test: "22222222-2222-2222-2222-222222222222"
      prod: "33333333-3333-3333-3333-333333333333"
```

### Built-in Variables

Use these in `replace_value` to reference runtime IDs:

| Variable | Resolves To |
|----------|-------------|
| `$workspace.$id` | Current target workspace ID |
| `$items.<Type>.<Name>.$id` | Item ID after publish |

**Example**:
```yaml
find_replace:
  - find_value: "placeholder-lakehouse-id"
    replace_value:
      dev: "$items.Lakehouse.SalesLH.$id"
      prod: "$items.Lakehouse.SalesLH.$id"
```

This is useful when notebooks or pipelines reference other items by ID — the ID changes per workspace, so the variable resolves it automatically.

---

## Running Deployments

```bash
# Deploy to specific environment
fab deploy --config config.yml --target_env dev

# Deploy to production
fab deploy --config config.yml --target_env prod

# Deploy with wait (waits for long-running operations)
fab deploy --config config.yml --target_env prod -w
```

---

## GitHub Actions Integration

### Service Principal Auth + Deploy

```yaml
name: Deploy to Microsoft Fabric
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Fabric CLI
        run: pip install ms-fabric-cli

      - name: Authenticate
        run: |
          fab auth login \
            -u ${{ secrets.FABRIC_CLIENT_ID }} \
            -p ${{ secrets.FABRIC_CLIENT_SECRET }} \
            --tenant ${{ secrets.FABRIC_TENANT_ID }}

      - name: Deploy to Dev
        run: fab deploy --config config.yml --target_env dev

      - name: Deploy to Prod
        if: github.ref == 'refs/heads/main'
        run: fab deploy --config config.yml --target_env prod
```

### Single Item Import (Simpler)

```yaml
- name: Import notebook to Fabric
  run: |
    pip install ms-fabric-cli
    fab auth login -u ${{ secrets.CLIENT_ID }} -p ${{ secrets.CLIENT_SECRET }} --tenant ${{ secrets.TENANT_ID }}
    fab import Production.Workspace/Data.Lakehouse -i ./artifacts/DataToImport.Lakehouse
```

---

## Azure Pipelines Integration

### Full Pipeline Example

```yaml
trigger:
  branches:
    include:
      - main

pool:
  vmImage: "ubuntu-latest"

stages:
  - stage: DeployDev
    displayName: "Deploy to Dev"
    jobs:
      - job: FabricDeploy
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: "3.12"

          - script: pip install ms-fabric-cli
            displayName: "Install Fabric CLI"

          - script: |
              fab auth login -u $(CLIENT_ID) -p $(CLIENT_SECRET) --tenant $(TENANT_ID)
            displayName: "Authenticate"

          - script: |
              fab deploy --config config.yml --target_env dev
            displayName: "Deploy to Dev workspace"

  - stage: DeployProd
    displayName: "Deploy to Prod"
    dependsOn: DeployDev
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - job: FabricDeploy
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: "3.12"

          - script: pip install ms-fabric-cli
            displayName: "Install Fabric CLI"

          - script: |
              fab auth login -u $(CLIENT_ID) -p $(CLIENT_SECRET) --tenant $(TENANT_ID)
            displayName: "Authenticate"

          - script: |
              fab deploy --config config.yml --target_env prod
            displayName: "Deploy to Prod workspace"
```

### Quick Job Trigger

```yaml
- script: |
    pip install ms-fabric-cli
    fab auth login -u $(CLIENT_ID) -p $(CLIENT_SECRET) --tenant $(TENANT_ID)
    fab job run ETL.Workspace/DailyRefresh.DataPipeline -w
  displayName: "Run Fabric pipeline"
```

---

## Repository Structure for Deploy

Recommended layout when using `fab deploy`:

```
repo/
├── config.yml           # deploy config
├── params.yml           # parameter file (find/replace)
├── Sales.Notebook/      # exported notebook definition
│   └── notebook-content.py
├── ETL.DataPipeline/    # exported pipeline definition
│   └── pipeline-content.json
└── Staging.Lakehouse/   # exported lakehouse definition
    └── lakehouse.json
```

Use `fab export` to create the item definition folders, then version-control them.

---

## Authentication Patterns for CI/CD

| Method | Command | Use Case |
|--------|---------|----------|
| Service Principal (secret) | `fab auth login -u <clientId> -p <clientSecret> --tenant <tenantId>` | CI/CD pipelines |
| Service Principal (certificate) | `fab auth login -u <clientId> --cert <path> --tenant <tenantId>` | High-security environments |
| Managed Identity | `fab auth login --identity` | Azure-hosted runners |
| Interactive (device code) | `fab auth login` | Local development only |

**Rule**: Never use interactive auth in CI/CD. Always use service principal or managed identity.

---

## Pre-Deploy Checklist

1. **Auth works**: `fab auth status` → confirms valid token
2. **Workspace exists**: `fab exists ws.TargetWorkspace` → returns `True`
3. **Items exported**: `fab export ws/item.Type -o ./repo/` → definition files on disk
4. **Config valid**: `core.workspace_id` matches target, `repository_directory` points to definitions
5. **Parameters set**: All `find_value` entries have correct `replace_value` per environment
6. **Capacity assigned**: Target workspace has capacity, or `default_capacity` is set
