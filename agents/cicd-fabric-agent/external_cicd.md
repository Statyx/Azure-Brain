# External CI/CD Platforms — Fabric CI/CD

## Overview

Fabric CI/CD can be automated from external platforms — GitHub Actions and Azure Pipelines — using service principal (SPN) authentication and the Fabric REST APIs. This file provides ready-to-use templates.

---

## Authentication for CI/CD

### Service Principal Setup

```
Prerequisites:
1. Register an App in Microsoft Entra ID
2. Create a client secret (or certificate)
3. Enable "Service principals can use Fabric APIs" in Fabric Admin Portal
4. Grant SPN the required workspace permissions (Member or Admin)
5. For deployment pipelines: add SPN as pipeline user

Store secrets:
├── GitHub → Repository Secrets (Settings > Secrets and variables > Actions)
│   ├── FABRIC_CLIENT_ID
│   ├── FABRIC_CLIENT_SECRET
│   └── FABRIC_TENANT_ID
└── Azure DevOps → Pipeline Variables (secret) or Variable Groups
    ├── $(CLIENT_ID)
    ├── $(CLIENT_SECRET)
    └── $(TENANT_ID)
```

### Auth Methods Comparison

| Method | Use Case | Platform |
|--------|----------|----------|
| Service Principal (secret) | Standard CI/CD | GitHub Actions, Azure Pipelines |
| Service Principal (certificate) | High-security | Azure Pipelines |
| Managed Identity | Azure-hosted runners | Azure Pipelines (Azure VM agents) |
| Interactive / device code | **NEVER in CI/CD** | Local dev only |

---

## GitHub Actions Templates

### Template 1: Full Pipeline — Git Commit + Deploy via Fabric CLI

```yaml
name: Fabric CI/CD Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.12"

jobs:
  validate:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - name: Validate item definitions
        run: |
          # Check .platform files are valid JSON
          find . -name ".platform" -exec python -m json.tool {} \;

      - name: Check for logicalId duplicates
        run: |
          python -c "
          import json, glob, sys
          ids = {}
          for f in glob.glob('**/.platform', recursive=True):
              data = json.load(open(f))
              lid = data.get('config', {}).get('logicalId', '')
              if lid in ids:
                  print(f'DUPLICATE logicalId {lid}: {ids[lid]} and {f}')
                  sys.exit(1)
              ids[lid] = f
          print(f'Validated {len(ids)} items — no duplicates')
          "

  deploy-dev:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Fabric CLI
        run: pip install ms-fabric-cli

      - name: Authenticate
        run: |
          fab auth login \
            -u ${{ secrets.FABRIC_CLIENT_ID }} \
            -p ${{ secrets.FABRIC_CLIENT_SECRET }} \
            --tenant ${{ secrets.FABRIC_TENANT_ID }}

      - name: Deploy to Dev
        run: fab deploy --config config.yml --target_env dev -w

  deploy-prod:
    runs-on: ubuntu-latest
    needs: deploy-dev
    if: github.ref == 'refs/heads/main'
    environment: production  # Requires manual approval
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Fabric CLI
        run: pip install ms-fabric-cli

      - name: Authenticate
        run: |
          fab auth login \
            -u ${{ secrets.FABRIC_CLIENT_ID }} \
            -p ${{ secrets.FABRIC_CLIENT_SECRET }} \
            --tenant ${{ secrets.FABRIC_TENANT_ID }}

      - name: Deploy to Prod
        run: fab deploy --config config.yml --target_env prod -w
```

### Template 2: REST API Deploy (No CLI)

```yaml
name: Fabric Deploy via REST API
on:
  workflow_dispatch:
    inputs:
      target_stage:
        description: "Target stage (0=Dev, 1=Test, 2=Prod)"
        required: true
        default: "1"

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Get access token
        id: auth
        run: |
          TOKEN=$(curl -s -X POST \
            "https://login.microsoftonline.com/${{ secrets.FABRIC_TENANT_ID }}/oauth2/v2.0/token" \
            -d "client_id=${{ secrets.FABRIC_CLIENT_ID }}" \
            -d "client_secret=${{ secrets.FABRIC_CLIENT_SECRET }}" \
            -d "scope=https://api.fabric.microsoft.com/.default" \
            -d "grant_type=client_credentials" | jq -r '.access_token')
          echo "token=$TOKEN" >> $GITHUB_OUTPUT

      - name: Deploy stage content
        run: |
          OPERATION_ID=$(curl -s -X POST \
            "https://api.fabric.microsoft.com/v1/deploymentPipelines/${{ secrets.PIPELINE_ID }}/deploy" \
            -H "Authorization: Bearer ${{ steps.auth.outputs.token }}" \
            -H "Content-Type: application/json" \
            -d '{
              "sourceStageId": "'${{ secrets.SOURCE_STAGE_ID }}'",
              "targetStageId": "'${{ secrets.TARGET_STAGE_ID }}'",
              "options": {
                "allowCreateArtifact": true,
                "allowOverwriteArtifact": true
              }
            }' | jq -r '.id')
          echo "Operation ID: $OPERATION_ID"

          # Poll until complete
          while true; do
            STATUS=$(curl -s \
              "https://api.fabric.microsoft.com/v1/deploymentPipelines/${{ secrets.PIPELINE_ID }}/operations/$OPERATION_ID" \
              -H "Authorization: Bearer ${{ steps.auth.outputs.token }}" | jq -r '.status')
            echo "Status: $STATUS"
            if [ "$STATUS" = "Succeeded" ] || [ "$STATUS" = "Failed" ]; then
              break
            fi
            sleep 10
          done

          if [ "$STATUS" != "Succeeded" ]; then
            echo "Deployment FAILED"
            exit 1
          fi
```

---

## Azure Pipelines Templates

### Template 1: Full Pipeline with Stage Gates

```yaml
trigger:
  branches:
    include:
      - main

pool:
  vmImage: "ubuntu-latest"

variables:
  pythonVersion: "3.12"

stages:
  - stage: Validate
    displayName: "Validate Item Definitions"
    jobs:
      - job: ValidateItems
        steps:
          - script: |
              find . -name ".platform" -exec python -m json.tool {} \;
            displayName: "Validate .platform files"

  - stage: DeployDev
    displayName: "Deploy to Dev"
    dependsOn: Validate
    jobs:
      - job: Deploy
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: $(pythonVersion)

          - script: pip install ms-fabric-cli
            displayName: "Install Fabric CLI"

          - script: |
              fab auth login \
                -u $(CLIENT_ID) \
                -p $(CLIENT_SECRET) \
                --tenant $(TENANT_ID)
            displayName: "Authenticate SPN"

          - script: |
              fab deploy --config config.yml --target_env dev -w
            displayName: "Deploy to Dev"

  - stage: DeployTest
    displayName: "Deploy to Test"
    dependsOn: DeployDev
    jobs:
      - job: Deploy
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: $(pythonVersion)

          - script: pip install ms-fabric-cli
            displayName: "Install Fabric CLI"

          - script: |
              fab auth login \
                -u $(CLIENT_ID) \
                -p $(CLIENT_SECRET) \
                --tenant $(TENANT_ID)
            displayName: "Authenticate SPN"

          - script: |
              fab deploy --config config.yml --target_env test -w
            displayName: "Deploy to Test"

  - stage: DeployProd
    displayName: "Deploy to Prod"
    dependsOn: DeployTest
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployProd
        environment: "Production"   # Requires approval
        strategy:
          runOnce:
            deploy:
              steps:
                - task: UsePythonVersion@0
                  inputs:
                    versionSpec: $(pythonVersion)

                - script: pip install ms-fabric-cli
                  displayName: "Install Fabric CLI"

                - script: |
                    fab auth login \
                      -u $(CLIENT_ID) \
                      -p $(CLIENT_SECRET) \
                      --tenant $(TENANT_ID)
                  displayName: "Authenticate SPN"

                - script: |
                    fab deploy --config config.yml --target_env prod -w
                  displayName: "Deploy to Prod"
```

### Template 2: Power BI Automation Tools Extension

```yaml
# Uses the Power BI automation tools Azure DevOps extension
# Install from: https://marketplace.visualstudio.com/items?itemName=ms-pbi-api.pbi-automation-tools
trigger:
  - main

pool:
  vmImage: "ubuntu-latest"

steps:
  - task: PowerBIActions@5
    displayName: "Deploy to Test stage"
    inputs:
      PowerBIServiceConnection: "FabricSPN"   # Service connection name
      Action: "DeployAll"
      PipelineName: "Sales BI Pipeline"
      SourceStageName: "Development"
      Options: |
        {
          "allowCreateArtifact": true,
          "allowOverwriteArtifact": true
        }
```

---

## PowerShell Automation Script

### End-to-End: Create Pipeline → Assign → Deploy

```powershell
# 1. Authenticate
$credential = New-Object PSCredential($clientId, (ConvertTo-SecureString $clientSecret -AsPlainText -Force))
Connect-PowerBIServiceAccount -ServicePrincipal -Credential $credential -TenantId $tenantId

# 2. Create pipeline
$pipeline = Invoke-PowerBIRestMethod -Url "pipelines" -Method Post -Body (@{
    displayName = "Sales Pipeline"
    description = "Automated sales deployment"
} | ConvertTo-Json) | ConvertFrom-Json

# 3. Assign workspaces to stages
@(
    @{ stage = 0; workspaceId = $devWorkspaceId },
    @{ stage = 1; workspaceId = $testWorkspaceId },
    @{ stage = 2; workspaceId = $prodWorkspaceId }
) | ForEach-Object {
    $url = "pipelines/{0}/stages/{1}/assignWorkspace" -f $pipeline.id, $_.stage
    $body = @{ workspaceId = $_.workspaceId } | ConvertTo-Json
    Invoke-PowerBIRestMethod -Url $url -Method Post -Body $body
}

# 4. Deploy Dev → Test
$deployBody = @{
    sourceStageOrder = 0
    options = @{
        allowCreateArtifact = $true
        allowOverwriteArtifact = $true
    }
} | ConvertTo-Json

$result = Invoke-PowerBIRestMethod -Url ("pipelines/{0}/DeployAll" -f $pipeline.id) -Method Post -Body $deployBody | ConvertFrom-Json

# 5. Poll for completion
$opUrl = "pipelines/{0}/Operations/{1}" -f $pipeline.id, $result.id
do {
    Start-Sleep -Seconds 5
    $op = Invoke-PowerBIRestMethod -Url $opUrl -Method Get | ConvertFrom-Json
} while ($op.Status -in @("NotStarted", "Executing"))

Write-Host "Deployment: $($op.Status)"
```

---

## Security Best Practices

| Practice | Detail |
|----------|--------|
| **Never log secrets** | Use `$GITHUB_OUTPUT` / pipeline variables, never `echo $SECRET` |
| **Rotate secrets** | Set expiry on client secrets (6–12 months max) |
| **Use environments** | GitHub environments + required reviewers for Prod |
| **Use approvals** | Azure DevOps environments + approval gates |
| **Minimum permissions** | SPN gets Workspace Member (not Admin unless needed) |
| **Audit trail** | Deployment pipeline operations are logged (GET /operations) |
| **Certificate auth** | Prefer certificates over secrets for high-security |

---

## Cross-References

- fab CLI deploy configs: `../fabric-cli-agent/cicd_deploy.md`
- Deployment pipeline API: `deployment_pipelines.md`
- Auth patterns: `../../fabric_api.md`
- SPN setup: `../../environment.md`
