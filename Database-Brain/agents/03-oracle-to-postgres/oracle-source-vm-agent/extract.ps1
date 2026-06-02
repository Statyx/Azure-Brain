$j = Get-Content "Database-Brain\agents\03-oracle-to-postgres\oracle-source-vm-agent\diag-out.json" -Raw | ConvertFrom-Json
$msg = $j.value[0].message
Set-Content -Path "Database-Brain\agents\03-oracle-to-postgres\oracle-source-vm-agent\diag.txt" -Value $msg -Encoding utf8
Write-Host "Written diag.txt ($($msg.Length) chars)"
