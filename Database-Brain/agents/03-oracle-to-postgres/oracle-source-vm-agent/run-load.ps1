$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
$here = "C:\Users\cdroinat\OneDrive - Microsoft\1 - Microsoft\01 - Architecture\-- 001 - Azure-Brain\Azure-Brain\Database-Brain\agents\03-oracle-to-postgres\oracle-source-vm-agent"
$script = Join-Path $here "load-demo-schema.sh"
Write-Host "[$(Get-Date -Format HH:mm:ss)] Running load-demo-schema.sh ..."
$json = & $az vm run-command invoke -g rg-demo-ora2pg -n vm-oracle-src --command-id RunShellScript --scripts "@$script" -o json
$out = Join-Path $here "load-demo-schema.out.json"
($json -join "`n") | Set-Content $out -Encoding utf8
Write-Host "[$(Get-Date -Format HH:mm:ss)] Done"
(Get-Content $out -Raw | ConvertFrom-Json).value[0].message
