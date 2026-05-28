# Quickstart — postgres-deploy-agent

Deploy Azure Database for PostgreSQL Flexible Server in ~5 minutes.

## 1. Store admin password in Key Vault

```bash
RG=rg-demo-pg
KV=kv-demo-pg
SERVER=pg-ora-target-$(openssl rand -hex 3)

PGPW=$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)
az keyvault secret set --vault-name $KV --name pg-admin-password --value "$PGPW"
echo "$PGPW" > .pgadmin-pw.txt  # do NOT commit
```

## 2. Deploy

```bash
# Get your Entra object ID
ENTRA_OID=$(az ad signed-in-user show --query id -o tsv)
ENTRA_UPN=$(az ad signed-in-user show --query userPrincipalName -o tsv)

az deployment group create \
  --resource-group $RG \
  --template-file postgres-flex.bicep \
  --parameters \
      serverName=$SERVER \
      adminPassword="$PGPW" \
      entraAdminObjectId="$ENTRA_OID" \
      entraAdminPrincipalName="$ENTRA_UPN" \
      allowedSourceIp="$(curl -s ifconfig.me)/32"
```

## 3. Run post-deploy script (extensions + migration schema)

```bash
FQDN=$(az deployment group show -g $RG -n postgres-flex --query properties.outputs.serverFqdn.value -o tsv)
PGPASSWORD="$PGPW" psql "host=$FQDN dbname=postgres user=pgadmin sslmode=require" -f scripts/post-deploy.sh
```

## 4. Validate

```bash
PGPASSWORD="$PGPW" psql "host=$FQDN dbname=postgres user=pgadmin sslmode=require" \
  -c "SHOW wal_level;" \
  -c "SELECT extname FROM pg_extension ORDER BY 1;"
# Expect: wal_level=logical, extensions include orafce, uuid-ossp, pgcrypto, pg_trgm
```

## Cost (demo profile)

- `Standard_B2ms` (Burstable, 2 vCPU / 8 GB) + 128 GB storage = **~70 EUR / month** if always on
- Stop server when not in use: `az postgres flexible-server stop -g $RG -n $SERVER` → ~5 EUR / month (storage only, 7-day max stop)
