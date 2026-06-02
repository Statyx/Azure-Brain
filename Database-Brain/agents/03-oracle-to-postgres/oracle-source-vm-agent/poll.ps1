$f = 'Database-Brain\agents\03-oracle-to-postgres\oracle-source-vm-agent\install-oracle-docker.sh.out.json'
for ($i = 0; $i -lt 80; $i++) {
    if (Test-Path $f) {
        Write-Host "FOUND after $($i * 10)s"
        break
    }
    Start-Sleep -Seconds 10
}
if (Test-Path $f) {
    (Get-Content $f -Raw | ConvertFrom-Json).value[0].message
} else {
    Write-Host "STILL-NOT-DONE after 800s"
}
