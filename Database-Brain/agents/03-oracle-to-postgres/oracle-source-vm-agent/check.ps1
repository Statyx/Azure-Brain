$ErrorActionPreference = "Continue"
$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
Write-Host "=== NSG Rules ===" -ForegroundColor Cyan
& $az network nsg rule list -g rg-demo-ora2pg --nsg-name vm-oracle-src-nsg --query "[].{name:name, prio:priority, port:destinationPortRange, src:sourceAddressPrefix, access:access, dir:direction}" -o table

Write-Host "`n=== NIC NSG attachment ===" -ForegroundColor Cyan
& $az network nic show -g rg-demo-ora2pg -n vm-oracle-src-nic --query "{nicNsg:networkSecurityGroup.id, subnet:ipConfigurations[0].subnet.id}" -o json

Write-Host "`n=== Effective rules on NIC ===" -ForegroundColor Cyan
& $az network nic list-effective-nsg -g rg-demo-ora2pg -n vm-oracle-src-nic --query "value[].effectiveSecurityRules[?destinationPortRange=='22' || contains(destinationPortRanges || '[]', '22')]" -o json
