#!/usr/bin/env pwsh
# Deploy Oracle 21c XE VM into existing rg-demo-ora2pg.
# Idempotent — re-running with same params is safe.
$ErrorActionPreference = "Stop"

$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
$RG = "rg-demo-ora2pg"
$KV = "kv-ora2pg-cb9f"
$VM = "vm-oracle-src"
$VMSIZE = "Standard_B4ms"
$SSHKEYFILE = "$env:USERPROFILE\.ssh\id_rsa.pub"
$IP = "167.220.197.39/32"
$BICEP = Join-Path $PSScriptRoot "oracle-vm.bicep"

if (-not (Test-Path $SSHKEYFILE)) { throw "SSH pubkey not found: $SSHKEYFILE" }
if (-not (Test-Path $BICEP))      { throw "Bicep not found: $BICEP" }

$pubkey = (Get-Content $SSHKEYFILE -Raw).Trim()
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$DEPLOY_NAME = "oracle-vm-$ts"

Write-Host "=== Deploying $DEPLOY_NAME ==="
Write-Host "  RG=$RG  VM=$VM  Size=$VMSIZE  IP=$IP  KV=$KV"
Write-Host ""

& $az deployment group create `
  --resource-group $RG `
  --name $DEPLOY_NAME `
  --template-file $BICEP `
  --parameters `
    vmName=$VM `
    sshPublicKey="$pubkey" `
    allowedSourceIp=$IP `
    keyVaultName=$KV `
    vmSize=$VMSIZE `
  --output json

if ($LASTEXITCODE -ne 0) { throw "Deployment failed with exit code $LASTEXITCODE" }

Write-Host ""
Write-Host "=== Outputs ==="
& $az deployment group show --resource-group $RG --name $DEPLOY_NAME --query "properties.outputs" -o json
