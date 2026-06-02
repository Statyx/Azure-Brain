$ErrorActionPreference = "Continue"
$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptFile = Join-Path $here $args[0]
$outFile = Join-Path $here "$($args[0]).out.json"
Write-Host "Running $($args[0]) on VM..." -ForegroundColor Cyan
$out = & $az vm run-command invoke -g rg-demo-ora2pg -n vm-oracle-src --command-id RunShellScript --scripts "@$scriptFile" -o json
$out | Set-Content $outFile -Encoding utf8
$msg = ($out | ConvertFrom-Json).value[0].message
$msg
