# Quickstart — oracle-to-postgres-copilot-modernization-agent

End-to-end **DB + Java app** migration in ~45 min, driven from VS Code, using Microsoft's
official 2026 toolchain (PG VS Code extension + GitHub Copilot App Modernization for Java).

## Prerequisites

See [prerequisites.md](prerequisites.md) for the exhaustive list. TL;DR:

- VS Code >= 1.95 with extensions: `ms-ossdata.vscode-pgsql`, `vscjava.vscode-java-pack`,
  `ms-azuretools.vscode-bicep`, `GitHub.copilot`, `GitHub.copilot-chat`, and the
  **App Modernization for Java** extension
- GitHub Copilot **Business or Enterprise** subscription
- Oracle source VM up (from `oracle-source-vm-agent`)
- PG Flex target up with **Entra Authentication enabled** (from `postgres-deploy-agent`)
- A Java app to migrate — recommended: fork of `spring-petclinic-oracle`

## Step 1 — Open the Java app in VS Code

```powershell
git clone https://github.com/<your-fork>/spring-petclinic-oracle.git
cd spring-petclinic-oracle
code .
```

Copy the recommended workspace settings:

```powershell
mkdir -Force .vscode
Copy-Item ..\..\..\Azure-Brain\Database-Brain\agents\03-oracle-to-postgres\oracle-to-postgres-copilot-modernization-agent\config\recommended-vscode-settings.json .vscode\settings.json
```

## Step 2 — Connect to Oracle source in the PG extension

1. Click the **elephant icon** in the Activity Bar
2. **+ Add Connection** → pick `Oracle` as source type
3. Connection string: `<oracle-fqdn>:1521/XEPDB1`
4. User: `SYSTEM`, Password: from KV (`az keyvault secret show --vault-name kv-oracle-demo --name oracle-sys-password --query value -o tsv`)
5. Click **Connect** — schemas `HR`, `SH`, `OE` should appear

## Step 3 — Connect to PG target

1. **+ Add Connection** → `Azure Database for PostgreSQL` → browse subscriptions
2. Pick the Flex Server → **Microsoft Entra ID** auth (no password)
3. Database: `oracle_migration` (created earlier by `postgres-deploy-agent`)

## Step 4 — Run the Oracle → PG migration wizard

1. Right-click the Oracle connection → **Migrate to PostgreSQL**
2. Select schema `HR` → Next
3. Review proposed type mappings (e.g. `NUMBER(8,2)` → `NUMERIC(8,2)`)
4. Click **Convert**
5. Wait ~2-5 min — wizard generates:
   - `out/hr-schema-pg.sql` (DDL)
   - `.github/postgre-migrations/hr/results/application_guidance/coding_notes.md`

**Review the `coding_notes.md` now** — open it, read all sections. Hand-edit if anything looks off.

## Step 5 — Apply schema to PG target

In the PG extension Query Editor, open `out/hr-schema-pg.sql`, target connection = PG, **Run**.

Verify: open Object Explorer → PG → `oracle_migration` → schemas → `hr` → tables visible.

## Step 6 — Load data (use Ora2Pg from the sibling agent)

The PG VS Code extension migrates schema only. For data, reuse the Ora2Pg path:

```powershell
ssh oracleadmin@<oracle-fqdn> 'bash run-copy-load.sh'
```

See [../oracle-to-postgres-migration-agent/README.md](../oracle-to-postgres-migration-agent/README.md) §5.

## Step 7 — Assess the Java app with Copilot Modernization

1. **Command Palette** → `Copilot Modernization: Assess Java Project`
2. Wait ~2-5 min
3. Open the report → look for **"Database Migration (Oracle)"** finding

## Step 8 — Run the Oracle → PG task

1. In the assessment report, click the **Database Migration (Oracle)** finding
2. Verify default solution is *"Migrate from Oracle DB to PostgreSQL"*
3. Confirm `coding_notes.md` is at the expected path (Hard rule #5 in `instructions.md`)
4. Click **Run Task**
5. Wait ~5-10 min while Copilot refactors:
   - `pom.xml` (drop `ojdbc`, add `org.postgresql:postgresql` + `com.azure:azure-identity-extensions`)
   - `application.properties` (JDBC URL + Managed Identity)
   - `@Query` annotations and SQL resource files

## Step 9 — Review every diff

VS Code Source Control panel shows all changes. For each file:

- ✅ Accept if pattern matches `coding_notes.md` guidance
- 🔁 If Copilot left password-based auth → reopen Copilot Chat: `@workspace Replace the password-based PostgreSQL connection with Azure Managed Identity using DefaultAzureCredential`
- 🔁 If Oracle-specific syntax remains (`DUAL`, `ROWNUM`, `SYSDATE`) → ask Copilot to redo

## Step 10 — Test locally with Testcontainers

```powershell
.\mvnw test -Dspring.profiles.active=postgres
```

Testcontainers spins up `postgres:16` locally, no Azure dependency. All tests should pass.

## Step 11 — Deploy and validate

(Out of scope for this agent — use App Service or Container Apps deploy agent.)

Smoke checks once deployed:

```powershell
# No password in env
az containerapp show -n petclinic-pg -g rg-oracle-demo --query properties.template.containers[0].env

# Hit an endpoint
curl https://petclinic-pg.<region>.azurecontainerapps.io/owners?lastName=Davis

# Compare with Oracle baseline
curl https://petclinic-oracle.<region>.azurecontainerapps.io/owners?lastName=Davis
# → should return identical row count and same names
```

## Time budget for full demo run

| Step | Time |
|---|---|
| 1-3 — Setup + connections | 10 min |
| 4-6 — DB migration | 15 min |
| 7-8 — Copilot assess + run | 10 min |
| 9 — Diff review | 5 min |
| 10 — Local test | 5 min |
| **Total** | **~45 min** |

## Demo narrative (for live talks)

> "Voilà une app Java Spring qui parle à Oracle. Je vais la moderniser vers PostgreSQL géré sur
> Azure, sans password — tout depuis VS Code, en deux clics.
>
> 1. L'extension PostgreSQL convertit le schéma — et écrit ses notes pour l'IA.
> 2. GitHub Copilot lit ces notes, refactore mon code Java, met du Managed Identity.
> 3. Test local en 30 secondes avec Testcontainers.
>
> Trois minutes pour la démo, trois jours pour le projet réel — versus trois mois en manuel."

## Troubleshooting

See `instructions.md` → **Common pitfalls**. Top 3 issues by frequency:

1. `coding_notes.md` not found by Copilot → path is wrong (case-sensitive)
2. App connects locally but fails in Azure with `pg_hba.conf` error → MI not added as PG Entra admin
3. Oracle connection in PG extension fails on Windows → missing Oracle Instant Client on PATH
