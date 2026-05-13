# Environment Setup

> **Copy this file to `environment.md` and adjust paths for your machine.**
> `environment.md` is gitignored.

## Python 3.12+

### Required Packages
```bash
pip install requests pyyaml faker azure-cli
```

Optional (for RTI demos):
```bash
pip install azure-eventhub
```

## Azure CLI

```bash
az login
az account set --subscription "<YOUR_SUBSCRIPTION_ID>"
```

Verify:
```bash
az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv
```

If the token command works, you're ready to deploy.

## Fabric Capacity

Your capacity must be **running** before any deployment:
```bash
az resource show --ids "/subscriptions/<SUB>/resourceGroups/<RG>/providers/Microsoft.Fabric/capacities/<NAME>" --query "properties.state" -o tsv
```

Expected output: `Active`

Minimum SKU: **F2** for demos, **F16** for production workloads.
