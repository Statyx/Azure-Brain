# CI/CD Pipeline Templates — GitHub Actions & Azure Pipelines

## Purpose

Ready-to-use pipeline YAML templates for deploying Fabric items via `fab` CLI.
Covers authentication, deployment, validation, and multi-environment promotion.

---

## GitHub Actions — Full Pipeline

### `.github/workflows/fabric-deploy.yml`

```yaml
name: Fabric CI/CD Deploy

on:
  push:
    branches: [main]
    paths:
      - 'fabric-artifacts/**'
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'test'
        type: choice
        options:
          - test
          - prod

env:
  PYTHON_VERSION: '3.12'
  FAB_VERSION: 'ms-fabric-cli'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install Fabric CLI
        run: pip install ${{ env.FAB_VERSION }}
      
      - name: Validate deploy config
        run: |
          echo "Checking deploy-config.yml syntax..."
          python -c "import yaml; yaml.safe_load(open('deploy-config.yml'))"
          echo "✅ Config valid"
      
      - name: Validate artifact structure
        run: |
          echo "Checking artifact directories..."
          for dir in fabric-artifacts/*/; do
            if [ -d "$dir" ]; then
              echo "  ✅ Found: $dir"
            fi
          done

  deploy-test:
    needs: validate
    if: github.ref == 'refs/heads/main' || github.event.inputs.environment == 'test'
    runs-on: ubuntu-latest
    environment: test
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install Fabric CLI
        run: pip install ${{ env.FAB_VERSION }}
      
      - name: Authenticate to Fabric (SPN)
        run: |
          fab auth login \
            -u ${{ secrets.FABRIC_SPN_CLIENT_ID }} \
            -p ${{ secrets.FABRIC_SPN_CLIENT_SECRET }} \
            --tenant ${{ secrets.FABRIC_TENANT_ID }}
      
      - name: Deploy to Test
        run: |
          fab deploy \
            --config deploy-config.yml \
            --target_env test \
            --params params-test.yml
      
      - name: Verify deployment
        run: |
          echo "Checking deployed items..."
          fab ls "${{ vars.TEST_WORKSPACE_NAME }}.Workspace" -l
          echo "✅ Test deployment verified"

  deploy-prod:
    needs: deploy-test
    if: github.event.inputs.environment == 'prod'
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install Fabric CLI
        run: pip install ${{ env.FAB_VERSION }}
      
      - name: Authenticate to Fabric (SPN)
        run: |
          fab auth login \
            -u ${{ secrets.FABRIC_SPN_CLIENT_ID }} \
            -p ${{ secrets.FABRIC_SPN_CLIENT_SECRET }} \
            --tenant ${{ secrets.FABRIC_TENANT_ID }}
      
      - name: Deploy to Production
        run: |
          fab deploy \
            --config deploy-config.yml \
            --target_env prod \
            --params params-prod.yml
      
      - name: Post-deploy validation
        run: |
          echo "Verifying production items..."
          fab ls "${{ vars.PROD_WORKSPACE_NAME }}.Workspace" -l
          echo "✅ Production deployment verified"
```

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `FABRIC_SPN_CLIENT_ID` | Service Principal (App Registration) client ID |
| `FABRIC_SPN_CLIENT_SECRET` | Service Principal secret |
| `FABRIC_TENANT_ID` | Azure AD tenant ID |

### Required GitHub Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TEST_WORKSPACE_NAME` | Test workspace display name | `SmartFactory-Test` |
| `PROD_WORKSPACE_NAME` | Prod workspace display name | `SmartFactory-Prod` |

---

## Azure Pipelines — Full Pipeline

### `azure-pipelines.yml`

```yaml
trigger:
  branches:
    include:
      - main
  paths:
    include:
      - fabric-artifacts/**

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '3.12'

stages:
  - stage: Validate
    displayName: 'Validate Artifacts'
    jobs:
      - job: ValidateConfig
        displayName: 'Validate Deploy Config'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: $(pythonVersion)
          
          - script: pip install ms-fabric-cli
            displayName: 'Install Fabric CLI'
          
          - script: |
              python -c "import yaml; yaml.safe_load(open('deploy-config.yml'))"
              echo "✅ Config valid"
            displayName: 'Validate YAML syntax'

  - stage: DeployTest
    displayName: 'Deploy to Test'
    dependsOn: Validate
    condition: succeeded()
    jobs:
      - deployment: DeployTestEnv
        displayName: 'Deploy to Test Environment'
        environment: 'fabric-test'
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self
                
                - task: UsePythonVersion@0
                  inputs:
                    versionSpec: $(pythonVersion)
                
                - script: pip install ms-fabric-cli
                  displayName: 'Install Fabric CLI'
                
                - script: |
                    fab auth login \
                      -u $(FABRIC_SPN_CLIENT_ID) \
                      -p $(FABRIC_SPN_CLIENT_SECRET) \
                      --tenant $(FABRIC_TENANT_ID)
                  displayName: 'Authenticate to Fabric'
                
                - script: |
                    fab deploy \
                      --config deploy-config.yml \
                      --target_env test \
                      --params params-test.yml
                  displayName: 'Deploy to Test'
                
                - script: |
                    fab ls "$(TEST_WORKSPACE_NAME).Workspace" -l
                  displayName: 'Verify deployment'

  - stage: DeployProd
    displayName: 'Deploy to Production'
    dependsOn: DeployTest
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployProdEnv
        displayName: 'Deploy to Production'
        environment: 'fabric-prod'  # Requires approval gate
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self
                
                - task: UsePythonVersion@0
                  inputs:
                    versionSpec: $(pythonVersion)
                
                - script: pip install ms-fabric-cli
                  displayName: 'Install Fabric CLI'
                
                - script: |
                    fab auth login \
                      -u $(FABRIC_SPN_CLIENT_ID) \
                      -p $(FABRIC_SPN_CLIENT_SECRET) \
                      --tenant $(FABRIC_TENANT_ID)
                  displayName: 'Authenticate to Fabric'
                
                - script: |
                    fab deploy \
                      --config deploy-config.yml \
                      --target_env prod \
                      --params params-prod.yml
                  displayName: 'Deploy to Production'
```

### Required Pipeline Variables (Variable Group: `fabric-secrets`)

| Variable | Secret | Description |
|----------|--------|-------------|
| `FABRIC_SPN_CLIENT_ID` | Yes | Service Principal client ID |
| `FABRIC_SPN_CLIENT_SECRET` | Yes | Service Principal secret |
| `FABRIC_TENANT_ID` | Yes | Azure AD tenant ID |
| `TEST_WORKSPACE_NAME` | No | Test workspace name |
| `PROD_WORKSPACE_NAME` | No | Prod workspace name |

---

## Deploy Config Template

### `deploy-config.yml`

```yaml
# Fabric CLI deploy configuration
version: 1.0

environments:
  dev:
    workspace: "SmartFactory-Dev"
    workspace_id: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  test:
    workspace: "SmartFactory-Test"
    workspace_id: "11111111-2222-3333-4444-555555555555"
  prod:
    workspace: "SmartFactory-Prod"
    workspace_id: "99999999-8888-7777-6666-555555555555"

items:
  # Deploy order matters — dependencies first
  - path: fabric-artifacts/LH_SmartFactory.Lakehouse
    type: Lakehouse
    
  - path: fabric-artifacts/NB_LoadData.Notebook
    type: Notebook
    
  - path: fabric-artifacts/SM_SmartFactory.SemanticModel
    type: SemanticModel
    publish_after_deploy: true
    
  - path: fabric-artifacts/RPT_Dashboard.Report
    type: Report
    publish_after_deploy: true

# Parameter substitution per environment
parameters:
  - find: "__WORKSPACE_ID__"
    replace_by_env:
      dev: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
      test: "11111111-2222-3333-4444-555555555555"
      prod: "99999999-8888-7777-6666-555555555555"
  
  - find: "__LAKEHOUSE_ID__"
    replace_by_env:
      dev: "dev-lakehouse-id"
      test: "test-lakehouse-id"
      prod: "prod-lakehouse-id"
```

---

## Git Branching Strategy

```
main (production-ready)
├── develop (integration branch)
│   ├── feature/new-report → merged to develop via PR
│   ├── feature/update-model → merged to develop via PR
│   └── fix/dax-formula → merged to develop via PR
└── release/v1.2 → cherry-pick from develop → merged to main
```

### Recommended Flow

1. **Feature branches** from `develop` for all changes
2. **PR to develop** with review (runs validation pipeline)
3. **develop → test** automatic deploy (CI trigger)
4. **develop → main** via release branch (manual merge + approval)
5. **main → prod** automatic deploy (requires environment approval gate)

---

## Exporting Items for CI/CD

```bash
# Export all items from Dev workspace
fab export "SmartFactory-Dev.Workspace/LH_SmartFactory.Lakehouse" -o ./fabric-artifacts/
fab export "SmartFactory-Dev.Workspace/SM_SmartFactory.SemanticModel" -o ./fabric-artifacts/
fab export "SmartFactory-Dev.Workspace/RPT_Dashboard.Report" -o ./fabric-artifacts/
fab export "SmartFactory-Dev.Workspace/NB_LoadData.Notebook" -o ./fabric-artifacts/

# Commit to Git
git add fabric-artifacts/
git commit -m "Export Fabric items for CI/CD"
git push origin develop
```

---

## Environment Variables for CI/CD (Alternative to `fab auth login`)

Set these environment variables in your CI/CD pipeline for auto-login:

```bash
export FAB_SPN_CLIENT_ID="<client_id>"
export FAB_SPN_CLIENT_SECRET="<client_secret>"
export FAB_TENANT_ID="<tenant_id>"

# fab commands will auto-authenticate using these variables
fab ls  # Works without explicit login
```
