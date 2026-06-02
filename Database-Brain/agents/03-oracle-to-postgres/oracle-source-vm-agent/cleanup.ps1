$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
$rg = "rg-demo-ora2pg"
$nsg = "vm-oracle-src-nsg"
$kv = "kv-ora2pg-cb9f"

Write-Host "==NSG=="
& $az network nsg rule delete -g $rg --nsg-name $nsg -n allow-ssh -o none 2>&1
Write-Host "Deleted allow-ssh"
& $az network nsg rule update -g $rg --nsg-name $nsg -n allow-oracle-listener --source-address-prefixes "*" -o none
Write-Host "Opened 1521 to *"
& $az network nsg rule list -g $rg --nsg-name $nsg --query "[].{name:name, port:destinationPortRange, source:sourceAddressPrefix}" -o table

Write-Host "`n==KV=="
$exists = & $az keyvault show -n $kv -g $rg --query name -o tsv 2>$null
if ($exists) {
    Write-Host "Deleting KV $kv ..."
    & $az keyvault delete -n $kv -g $rg -o none
    Write-Host "Purging KV $kv ..."
    & $az keyvault purge -n $kv --no-wait -o none 2>&1
    Write-Host "KV deleted (purge may take ~1min)"
} else {
    Write-Host "KV $kv not found (already gone)"
}

Write-Host "`n==DONE=="
