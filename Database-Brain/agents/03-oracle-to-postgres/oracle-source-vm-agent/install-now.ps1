$ErrorActionPreference = "Continue"
$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
$here = "C:\Users\cdroinat\OneDrive - Microsoft\1 - Microsoft\01 - Architecture\-- 001 - Azure-Brain\Azure-Brain\Database-Brain\agents\03-oracle-to-postgres\oracle-source-vm-agent"
$scriptFile = Join-Path $here "install-oracle-docker.sh"
$outFile = Join-Path $here "install-oracle-docker.sh.out.json"
Write-Host "[$(Get-Date -Format HH:mm:ss)] Launching Run Command on VM..."
Write-Host "Script: $scriptFile"
Write-Host "Out:    $outFile"
$out = & $az vm run-command invoke -g rg-demo-ora2pg -n vm-oracle-src --command-id RunShellScript --scripts "@$scriptFile" -o json 2>&1
Write-Host "[$(Get-Date -Format HH:mm:ss)] az returned. Length=$([string]::Join('',$out).Length)"
($out -join "`n") | Set-Content $outFile -Encoding utf8
Write-Host "Wrote $outFile"
try {
    $msg = (Get-Content $outFile -Raw | ConvertFrom-Json).value[0].message
    Write-Host "----- MESSAGE -----"
    $msg
} catch {
    Write-Host "Could not parse JSON, raw output:"
    Get-Content $outFile -Raw
}
