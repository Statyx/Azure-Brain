# Prerequisites — oracle-to-postgres-copilot-modernization-agent

## VS Code

- **VS Code >= 1.95** — required for the PG extension preview features
  Verify: `code --version`

## VS Code Extensions

Install from Marketplace (Ctrl+Shift+X). Exact IDs:

| ID | Name | Why |
|---|---|---|
| `ms-ossdata.vscode-pgsql` | PostgreSQL | Connection, query editor, **Oracle → PG migration wizard**, generates `coding_notes.md`, `@pgsql` Copilot chat participant |
| `GitHub.copilot` | GitHub Copilot | AI code completion |
| `GitHub.copilot-chat` | GitHub Copilot Chat | Chat surface for `@pgsql` and `@workspace` |
| `vscjava.vscode-java-pack` | Extension Pack for Java | Java language support + Maven + JUnit |
| `vscjava.vscode-gradle` | Gradle for Java | (only if app uses Gradle instead of Maven) |
| `ms-azuretools.vscode-bicep` | Bicep | For infra-as-code (PG Flex, App Service) |
| `ms-azuretools.vscode-azureresourcegroups` | Azure Resources | Browse + manage Azure resources |
| **App Modernization for Java** | (search Marketplace: "GitHub Copilot app modernization") | The migration task surface |
| `ms-vscode-remote.vscode-remote-extensionpack` | Remote Development | (optional) work in WSL or SSH to Oracle VM |

One-shot install command:

```powershell
code --install-extension ms-ossdata.vscode-pgsql `
     --install-extension GitHub.copilot `
     --install-extension GitHub.copilot-chat `
     --install-extension vscjava.vscode-java-pack `
     --install-extension ms-azuretools.vscode-bicep `
     --install-extension ms-azuretools.vscode-azureresourcegroups
# App Modernization for Java: install via Marketplace UI (search the exact name)
```

## Subscriptions / Accounts

| Item | Tier | Notes |
|---|---|---|
| GitHub Copilot | **Business or Enterprise** | Free tier does NOT expose the App Modernization task surface |
| Azure subscription | Any | Must have permission to read PG Flex + assign roles |
| Azure AD / Entra ID | User or Service Principal | Used for PG Flex Entra auth + Managed Identity on the deployed app |

## Local tools

| Tool | Version | Notes |
|---|---|---|
| Java JDK | 17 or 21 (LTS) | Required by `spring-petclinic` and most Spring Boot 3.x apps |
| Maven | 3.9+ | Or use `mvnw` wrapper from the repo |
| Docker Desktop | latest | For Testcontainers local PG validation (step 10) |
| Azure CLI | 2.60+ | `az --version` — used for KV access, PG operations |
| Git | 2.40+ | Clone the Java app fork |

## Native client libraries

### Windows

- **Oracle Instant Client Basic Light** — required by the PG VS Code extension to read Oracle metadata.
  Download from oracle.com (free), unzip to e.g. `C:\oracle\instantclient_21_13`, add to PATH:
  ```powershell
  [Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";C:\oracle\instantclient_21_13", "User")
  ```
  Restart VS Code after.

### macOS / Linux

- Oracle Instant Client Basic via brew (mac) or rpm/deb (Linux). Symlink `libclntsh.dylib` / `.so`
  into a directory on `DYLD_LIBRARY_PATH` / `LD_LIBRARY_PATH`.

## Azure side prep

Required BEFORE running the demo:

1. **PG Flex Server with Entra Auth enabled**
   ```powershell
   az postgres flexible-server update -n <pg-server> -g <rg> `
     --active-directory-auth Enabled --password-auth Enabled
   ```
2. **Add yourself as PG Entra admin** (for hands-on testing)
   ```powershell
   az postgres flexible-server ad-admin create -g <rg> -s <pg-server> `
     --display-name $(az ad signed-in-user show --query userPrincipalName -o tsv) `
     --object-id $(az ad signed-in-user show --query id -o tsv)
   ```
3. **Managed Identity for the deployed app** — create at deploy time, then add it as Entra admin too
   (same command, different `--display-name` / `--object-id`)

## Sample Java app (recommended)

| Repo | Why |
|---|---|
| [spring-petclinic-oracle](https://github.com/spring-petclinic/spring-petclinic-oracle) (community fork) | Well-known to Copilot, has Oracle JDBC, small enough for a 45-min demo |
| [WeatherForecast Java starter with Oracle](https://github.com/microsoft/azure-spring-boot-samples) | Smaller, less storytelling potential |
| Your own app | Best for prospect demos — but Copilot quality varies |

Clone:

```powershell
git clone https://github.com/spring-petclinic/spring-petclinic-oracle.git
cd spring-petclinic-oracle
code .
```

## Verification checklist

Run these BEFORE starting the demo to avoid surprises:

```powershell
# 1. Code + Copilot
code --version                                  # >= 1.95
code --list-extensions | findstr "ms-ossdata"  # has vscode-pgsql
code --list-extensions | findstr "GitHub"      # has copilot + copilot-chat

# 2. Java + Maven
java -version                                   # 17 or 21
mvn -v                                          # 3.9+

# 3. Docker (for Testcontainers later)
docker ps                                       # daemon running

# 4. Azure auth
az account show                                 # logged in
az postgres flexible-server show -n <pg> -g <rg> --query authConfig.activeDirectoryAuth
# → "Enabled"

# 5. Oracle Instant Client (Windows only)
where oci.dll                                   # should print a path
```

If any check fails → fix BEFORE starting the demo. Live troubleshooting kills momentum.
