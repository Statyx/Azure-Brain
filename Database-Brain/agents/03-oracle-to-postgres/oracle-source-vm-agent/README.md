# Quickstart — oracle-source-vm-agent

Deploy Oracle Database 21c Express Edition on Azure VM in ~15 minutes.

## Prerequisites

- Azure CLI logged in (`az login`)
- Existing Resource Group + Key Vault with RBAC permission model
- SSH key pair (`~/.ssh/id_rsa.pub`)
- Your operator public IP (`curl -s ifconfig.me`)

## 1. Store Oracle SYS password in Key Vault

```bash
RG=rg-demo-oracle
KV=kv-demo-oracle

SYSPW=$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)
az keyvault secret set --vault-name $KV --name oracle-sys-password --value "$SYSPW"

# Save locally for SSH testing (do NOT commit)
echo "$SYSPW" > .oracle-syspw.txt
```

## 2. Deploy

```bash
az deployment group create \
  --resource-group $RG \
  --template-file oracle-vm.bicep \
  --parameters \
      vmName=vm-oracle-src \
      sshPublicKey="$(cat ~/.ssh/id_rsa.pub)" \
      allowedSourceIp="$(curl -s ifconfig.me)/32" \
      keyVaultName=$KV
```

Outputs:
- `vmFqdn` — e.g. `vm-oracle-src.francecentral.cloudapp.azure.com`
- `oracleConnectionString` — e.g. `vm-oracle-src.francecentral.cloudapp.azure.com:1521/XEPDB1`

## 3. Wait for cloud-init (~10 min)

```bash
FQDN=$(az deployment group show -g $RG -n oracle-vm --query properties.outputs.vmFqdn.value -o tsv)
ssh oracleadmin@$FQDN 'tail -f /var/log/oracle-install.log'
# Look for: "==> Oracle XE install COMPLETE"
```

## 4. Validate

```bash
ssh oracleadmin@$FQDN "sqlplus -s system/$(cat .oracle-syspw.txt)@localhost:1521/XEPDB1 <<< 'select count(*) from hr.employees;'"
# Should return 107
```

## Cost

- VM `Standard_D4s_v5` (16 GB) + 128 GB Premium SSD = **~150 EUR / month** if always on
- Demo pattern: stop VM after demo → `az vm deallocate -g $RG -n vm-oracle-src` → ~15 EUR / month (disks only)

## Cleanup

```bash
az group delete -g $RG --yes --no-wait
```
