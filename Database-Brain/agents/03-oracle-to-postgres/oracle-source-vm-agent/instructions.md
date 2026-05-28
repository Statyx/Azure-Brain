# oracle-source-vm-agent

## Role

Deploy and configure an **Oracle Database 21c Express Edition (XE)** instance on an Azure Linux VM,
used as the **source database** for Oracle → PostgreSQL migration demos and labs.

Not for production. XE is free, install is fully scripted, no licence to manage.

## Scope

| In scope | Out of scope |
|---|---|
| VM (Oracle Linux 8) + data disk | Oracle EE / RAC / Data Guard |
| Oracle XE 21c silent install via cloud-init | High availability, geo-replication |
| Listener 1521, SYS/SYSTEM users | Production hardening (CIS L2, FIPS) |
| Sample schemas HR, SH, OE loaded from `oracle/db-sample-schemas` | Custom application schemas |
| Outputs: connection string, hostname, port | Backup strategy (use RMAN externally if needed) |

## Hard rules

1. **Oracle XE 21c only** — version `21.3.0.0.0`. Other versions break the silent install script.
2. **Oracle Linux 8** (Marketplace publisher `Oracle`, offer `Oracle-Linux`, SKU `ol88-lvm-gen2`).
3. **Listener on 1521 always**, never change the port — Ora2Pg / DMS connectors assume default.
4. **CDB/PDB naming locked**: CDB = `XE`, PDB = `XEPDB1`. Sample schemas land in `XEPDB1`.
5. **Passwords**: SYS / SYSTEM share the same password, generated at deploy and stored in Azure Key Vault. NEVER write password into Bicep parameter files committed to git.
6. **NSG**: SSH (22) and Oracle (1521) open ONLY to the operator IP (`allowedSourceIp` parameter). No `*` source rule.
7. **State**: deployment is idempotent — re-running `az deployment group create` updates without recreating disks.
8. **Firewall belt-and-braces**: even with NSG, cloud-init MUST open `firewalld` for tcp/1521 inside the OS — Oracle Linux 8 ships `firewalld` enabled and will silently drop traffic to 1521 otherwise.
9. **Easy Connect for clients**: external tools (Ora2Pg, DMS, SQL Developer) MUST use Easy Connect format `host:1521/XEPDB1`, NOT TNS aliases. TNS triggers `DPY-4027` in python-oracledb thin mode.
10. **Password special chars**: SYS / sample-schema passwords containing `!` MUST be double-quoted in SQL (`IDENTIFIED BY "Pw!"`) AND escaped in shell (`sqlplus -S "user/\"Pw!\""`). Single-layer quoting silently truncates or errors `ORA-01017`.
11. **DB auto-start on reboot**: Oracle XE 21c registers a systemd unit `oracle-xe-21c.service` but it's **disabled by default**. cloud-init runs `systemctl enable oracle-xe-21c` so DB comes back up after VM stop/start. Without this → `ORA-01034: ORACLE not available` on every reboot.

## Inputs

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `resourceGroupName` | string | — | Pre-existing RG |
| `location` | string | `francecentral` | Any region with `D4s_v5` |
| `vmName` | string | `vm-oracle-src` | Becomes hostname + listener service name |
| `adminUsername` | string | `oracleadmin` | Linux user, sudo-enabled |
| `sshPublicKey` | string | — | Required, no password auth |
| `allowedSourceIp` | string | — | `x.x.x.x/32` for SSH + 1521 |
| `vmSize` | string | `Standard_D4s_v5` | 4 vCPU / 16 GB |
| `dataDiskSizeGb` | int | `128` | Premium SSD P10 |
| `keyVaultName` | string | — | Existing KV where the Oracle password is stored as secret `oracle-sys-password` |
| `loadSampleSchemas` | bool | `true` | Run HR / SH / OE load after install |

## Outputs

| Output | Description |
|---|---|
| `vmFqdn` | DNS name of the VM (e.g. `vm-oracle-src.francecentral.cloudapp.azure.com`) |
| `oracleConnectionString` | `<fqdn>:1521/XEPDB1` |
| `sysUserSecretRef` | Key Vault secret URI for the SYS password |

## Files in this agent folder

- [instructions.md](instructions.md) — this file
- [oracle-vm.bicep](oracle-vm.bicep) — main deployment template
- [cloud-init.yaml](cloud-init.yaml) — VM init: install Oracle XE + load sample schemas
- [scripts/install-oracle-xe.sh](scripts/install-oracle-xe.sh) — silent install steps invoked by cloud-init
- [scripts/load-sample-schemas.sh](scripts/load-sample-schemas.sh) — clone `oracle/db-sample-schemas` and load HR / SH / OE
- [README.md](README.md) — quickstart deployment guide

## Deployment workflow

```bash
# 1. Generate SYS password and store in Key Vault
SYSPW=$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)
az keyvault secret set --vault-name <kv> --name oracle-sys-password --value "$SYSPW"

# 2. Deploy VM
az deployment group create \
  --resource-group <rg> \
  --template-file oracle-vm.bicep \
  --parameters \
      vmName=vm-oracle-src \
      sshPublicKey="$(cat ~/.ssh/id_rsa.pub)" \
      allowedSourceIp="$(curl -s ifconfig.me)/32" \
      keyVaultName=<kv>

# 3. Wait ~10 min for cloud-init to finish Oracle XE install
ssh oracleadmin@<vmFqdn> 'tail -f /var/log/oracle-install.log'

# 4. Validate
ssh oracleadmin@<vmFqdn> 'sqlplus system/$SYSPW@localhost:1521/XEPDB1 <<< "select user from dual;"'
```

## Common pitfalls

- **Swap space**: Oracle XE installer requires >= 2 GB swap. cloud-init creates 4 GB swapfile on `/dev/sdc` before running installer.
- **SELinux**: leave in `enforcing` — Oracle XE 21c RPM is SELinux-aware.
- **Kernel parameters**: `oracle-database-preinstall-21c` RPM (installed first) sets all `sysctl` correctly. Do not override.
- **Listener binding**: by default binds to `localhost` (IPv6 `:::1521`) only. Post-install step rewrites `listener.ora` with explicit `HOST = 0.0.0.0` to bind on IPv4 all-interfaces. Without this, `tnsping` succeeds locally but `Test-NetConnection` from outside fails with timeout.
- **firewalld vs NSG**: Oracle Linux 8 has `firewalld` active. NSG opening 1521 is NOT sufficient — must also `firewall-cmd --add-port=1521/tcp --permanent && firewall-cmd --reload` inside the VM.
- **NSG order**: open 1521 AFTER cloud-init confirms listener is up, otherwise health checks log noisy auth failures.
- **Password `!` truncation**: bash interprets `!` as history expansion in interactive shells. Always quote: `export ORA_PWD='Pw!123'` not `export ORA_PWD="Pw!123"`.
- **VM stop → DB stop**: stopping VM (or `sudo shutdown`) does NOT cleanly shut Oracle. Use `lifecycle/stop-vm.sh` which runs `shutdown immediate` first, then `az vm stop`.
- **Cost when stopped**: deallocated VM costs $0 compute, but data disk (~$30/mo for P10 128 GB) + static IP (~$4/mo) keep accruing. Acceptable for a demo.

## Lessons from production (Statyx field experience)

These patterns come from a tested Oracle 19c EE deployment on Azure (PowerShell-based, different toolchain but
same target). Source: [`reference/Tools_for_orcl_to_pg`](../../../../reference/Tools_for_orcl_to_pg) by Emmanuel Deletang.
We reuse the **bug taxonomy and gotchas** even though our scaffold uses XE 21c + Bicep instead of EE 19c + PowerShell.

| Symptom client | Root cause | Fix in this agent |
|---|---|---|
| `DPY-6005: cannot connect, timeout` | DB not running (VM up, listener up, instance down) | cloud-init enables `oracle-xe-21c.service` at boot (Hard rule #11) |
| `DPY-4027: no configuration directory specified` | Client uses TNS alias instead of Easy Connect | Output `oracleConnectionString` is Easy Connect format (Hard rule #9) |
| `ORA-01017: invalid username/password` with `!` in pwd | Password not double-quoted in SQL or shell | Documented in Hard rule #10 + applied in `load-sample-schemas.sh` |
| `ORA-01034: ORACLE not available` after VM restart | `oracle-xe-21c.service` disabled by default | cloud-init runs `systemctl enable` (Hard rule #11) |
| TCP timeout from outside, OK locally | Listener bound IPv6-only, OR firewalld blocking | Listener rewritten to 0.0.0.0 + firewalld port opened (pitfalls above) |
| `terms not accepted` (if pivoting to EE) | Marketplace image needs explicit ToS accept | Not applicable for XE (RPM install), but flagged in `oracle-source-vm-19c-agent` (planned) |

## Validation checklist

- [ ] `sqlplus system/<pw>@<fqdn>:1521/XEPDB1` connects
- [ ] `select count(*) from hr.employees;` returns 107
- [ ] `select count(*) from sh.sales;` returns ~918k
- [ ] Listener visible from operator IP: `tnsping <fqdn>:1521/XEPDB1`

## Related agents

- [postgres-deploy-agent](../../02-postgres/postgres-deploy-agent/instructions.md) — target environment
- [oracle-to-postgres-migration-agent](../oracle-to-postgres-migration-agent/instructions.md) — Ora2Pg + DMS migration pipeline
