# Known Issues & Troubleshooting — Fabric CLI

---

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| `0` | Success | — |
| `1` | General Error | Check error message, review command syntax |
| `2` | Usage Error / Cancelled | Wrong arguments or user cancelled (`Ctrl+C`) |
| `4` | Authentication Required | Run `fab auth login` or check token expiry |

**CI/CD tip**: Check exit code after every `fab` call. Code `4` means re-authenticate.

---

## Common Issues & Fixes

### 1. Encrypted Cache Error

**Symptom**: `Error: Could not decrypt cache` or similar encryption error on Linux/container.

**Fix**:
```bash
fab config set encryption_fallback_enabled true
```

**Why**: The default token cache uses OS-level encryption (DPAPI on Windows, libsecret on Linux). Headless environments and containers lack a keyring, causing this error. The fallback stores tokens unencrypted — acceptable for CI/CD runners.

---

### 2. "Item Not Found" Despite Correct Name

**Symptom**: `fab ls ws.MyWorkspace/nb.MyNotebook` → "Not found"

**Possible causes**:
- **Missing type suffix**: Must use `nb.MyNotebook`, not just `MyNotebook`
- **Case sensitivity**: Item names are case-sensitive in the path
- **Stale cache**: Run `fab config set cache_enabled false` or restart CLI

**Fix**: Verify exact name with `fab ls ws.MyWorkspace -q "[?type=='Notebook']"`.

---

### 3. Path Syntax Errors

**Symptom**: "Invalid path" or unexpected behavior with paths.

**Rules**:
- Workspace: `ws.MyWorkspace` or `MyWorkspace.Workspace`
- Item: `ws.MyWorkspace/nb.MyNotebook` 
- OneLake file: `ws.MyWorkspace/lh.MyLakehouse/Files/path/to/file.csv`
- Delta table: `ws.MyWorkspace/lh.MyLakehouse/Tables/tablename`
- **Never mix** OneLake URL paths (`https://onelake.dfs.fabric.microsoft.com/...`) with CLI paths

**Tip**: Use `fab desc ws.MyWorkspace/lh.MyLakehouse` to verify path resolution.

---

### 4. Authentication Expiry in Long CI/CD Runs

**Symptom**: Job starts fine but fails mid-execution with exit code `4`.

**Cause**: Service principal token expired (default 1h lifetime).

**Mitigation**:
- Re-authenticate before each major step
- Use `fab auth status` to check remaining token life
- Keep individual `fab` operations short (deploy per item, not bulk)

---

### 5. `fab deploy` Skips Items

**Symptom**: Deploy runs but some items aren't published.

**Check**:
1. `item_types_in_scope` — is the item type listed?
2. `publish.exclude_regex` — does the item name match the exclusion pattern?
3. `publish.skip.<env>` — is the target environment set to `true`?
4. `repository_directory` — does the folder path contain the item definition?

---

### 6. OneLake `Files/` vs `Tables/` Confusion

**Symptom**: Upload to Tables path succeeds but table is unreadable, or vice versa.

**Rules**:
- `Files/` = raw file storage (CSV, Parquet, images, anything)
- `Tables/` = **Delta Lake only** — must be valid Delta format
- Uploading a CSV to `Tables/` does NOT create a Delta table — use `fab table load` instead

**Correct patterns**:
```bash
# Upload raw CSV → Files/
fab cp data.csv ws/lh.Lakehouse/Files/data.csv

# Load CSV → Delta table (Tables/)
fab table load Tables/sales --file data.csv
```

---

### 7. `fab import` Fails with "Item Already Exists"

**Symptom**: Import fails because the item already exists in the workspace.

**Fix**: `fab import` updates existing items by default. If it still fails:
- Check that the item type matches (can't import a Notebook definition over a Pipeline)
- Check workspace permissions (need Contributor or above)
- Use `fab exists ws/item.Type` to verify current state
- Use `-f` (force) flag if available for the operation

---

### 8. Interactive Mode Commands Fail in Scripts

**Symptom**: Commands work in interactive mode but fail in shell scripts.

**Cause**: Interactive mode uses relative paths from `fab cd` context. Scripts run in `command_line` mode where every path must be fully qualified.

**Fix**: Always use full paths in scripts:
```bash
# Bad (relies on interactive cd context)
fab ls nb.MyNotebook

# Good (fully qualified)
fab ls ws.MyWorkspace/nb.MyNotebook
```

---

### 9. Slow Listing on Large Workspaces

**Symptom**: `fab ls ws.LargeWorkspace` takes very long.

**Mitigations**:
- Use JMESPath filter: `fab ls ws.LargeWorkspace -q "[?type=='Notebook']"`
- Enable caching: `fab config set cache_enabled true`
- Avoid `-l` (long format) unless needed — it makes extra API calls per item

---

### 10. Table Optimize/Vacuum Permissions

**Symptom**: `fab table optimize` or `fab table vacuum` fails with permission error.

**Cause**: Table operations require at least Contributor access on the Lakehouse.

**Fix**: Verify role with `fab acl ws.MyWorkspace -l` and ensure the identity has Contributor or Admin.

---

## Token Cache Location

| OS | Path |
|----|------|
| Windows | `%USERPROFILE%\.config\fab\cache.bin` |
| Linux/macOS | `~/.config/fab/cache.bin` |

To clear auth state: delete `cache.bin` and re-authenticate.

---

## Reporting Bugs

GitHub Issues: `https://github.com/microsoft/fabric-cli/issues`

Include:
- `fab --version` output
- Full command that failed
- Error message / exit code
- OS and Python version
