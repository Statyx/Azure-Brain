$ErrorActionPreference = "Continue"
$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptFile = Join-Path $here "diag.sh"
Write-Host "Running on VM via Azure agent..." -ForegroundColor Cyan
$out = & $az vm run-command invoke -g rg-demo-ora2pg -n vm-oracle-src --command-id RunShellScript --scripts "@$scriptFile" -o json
$out | Set-Content "$here\diag-out.json" -Encoding utf8
$parsed = $out | ConvertFrom-Json
$parsed.value[0].message
