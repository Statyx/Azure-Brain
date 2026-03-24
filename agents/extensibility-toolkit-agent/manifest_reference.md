# Manifest Reference — Fabric Extensibility Toolkit

## Manifest Overview

The Fabric workload manifest is a **NuGet package** (`.nupkg`) containing two folders:

```
[WorkloadName].nupkg
├── BE/                              # Backend manifests (XML)
│   ├── WorkloadManifest.xml         # Workload-level backend config
│   └── [ItemName]Item.xml           # Per-item backend config (one per item type)
│
└── FE/                              # Frontend manifests (JSON)
    ├── Product.json                 # Workload-level frontend config
    ├── [ItemName]Item.json          # Per-item frontend config (one per item type)
    └── assets/                      # Icons, images, thumbnails
        ├── workload-icon.png
        ├── item-icon-small.png
        ├── item-icon-medium.png
        └── item-icon-large.png
```

---

## Package Limits

| Constraint | Limit |
|-----------|-------|
| Max items per workload | **10** |
| Max asset file size | **1.5 MB** each |
| Max total assets | **15** files |
| Max package size | **20 MB** |
| Filename length | **≤32 characters** |
| Filename characters | Alphanumeric + hyphens only |

---

## Workload-Level Manifests

### WorkloadManifest.xml (Backend)

The top-level backend configuration for the workload.

```xml
<?xml version="1.0" encoding="utf-8"?>
<WorkloadManifest>
  <!-- Unique workload identifier: [Organization].[WorkloadName] -->
  <Name>Contoso.DataQuality</Name>
  
  <!-- Display metadata -->
  <DisplayName>Contoso Data Quality</DisplayName>
  <Description>Data quality monitoring and remediation for Fabric</Description>
  <Version>1.0.0</Version>
  
  <!-- Authentication -->
  <AADApp>
    <AppId>xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx</AppId>
    <RedirectUri>https://your-app.azurewebsites.net/auth/callback</RedirectUri>
  </AADApp>
  
  <!-- Optional: Remote Lifecycle Notifications (Preview) -->
  <NotificationEndpoint>
    <Url>https://your-backend.azurewebsites.net/api/notifications</Url>
    <Events>
      <Event>Created</Event>
      <Event>Updated</Event>
      <Event>Deleted</Event>
    </Events>
  </NotificationEndpoint>
  
  <!-- Optional: Fabric Scheduler / Remote Jobs (Preview) -->
  <Jobs>
    <JobType>
      <Name>DataQualityCheck</Name>
      <DisplayName>Data Quality Check</DisplayName>
    </JobType>
  </Jobs>
</WorkloadManifest>
```

### Product.json (Frontend)

The top-level frontend configuration for the workload.

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/workload/product.schema.json",
  "name": "Contoso.DataQuality",
  "displayName": "Contoso Data Quality",
  "description": "Data quality monitoring and remediation for Fabric",
  "version": "1.0.0",
  "icon": {
    "name": "contoso-dq-icon"
  },
  "category": "Data Management",
  "homePage": {
    "path": "/home"
  },
  "assets": {
    "contoso-dq-icon": "assets/workload-icon.png"
  }
}
```

---

## Item-Level Manifests

### [ItemName]Item.xml (Backend)

Per-item backend manifest. One file per item type.

```xml
<?xml version="1.0" encoding="utf-8"?>
<ItemManifest>
  <!-- Item type name (must match frontend manifest name) -->
  <Name>QualityRule</Name>
  
  <!-- Display metadata -->
  <DisplayName>Quality Rule</DisplayName>
  <Description>Define data quality rules and thresholds</Description>
  
  <!-- Icons (referenced from FE/assets/) -->
  <SmallIcon>assets/quality-rule-small.png</SmallIcon>
  <MediumIcon>assets/quality-rule-medium.png</MediumIcon>
  <LargeIcon>assets/quality-rule-large.png</LargeIcon>
  
  <!-- Feature flags -->
  <SupportedInMonitoringHub>true</SupportedInMonitoringHub>
  
  <!-- Optional: OneLake storage configuration -->
  <OneLakeStorage>
    <Tables>true</Tables>
    <Files>true</Files>
  </OneLakeStorage>
  
  <!-- Optional: Job types this item supports -->
  <SupportedJobTypes>
    <JobType>DataQualityCheck</JobType>
  </SupportedJobTypes>
</ItemManifest>
```

### [ItemName]Item.json (Frontend)

Per-item frontend manifest. One file per item type.

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/workload/item.schema.json",
  "name": "QualityRule",
  "displayName": "Quality Rule",
  "description": "Define data quality rules and thresholds",
  "editor": {
    "path": "/items/QualityRule/QualityRuleItemEditor"
  },
  "icon": {
    "name": "quality-rule-icon"
  },
  "supportedFeatures": {
    "sharing": true,
    "lineage": true
  },
  "contextMenu": {
    "actions": [
      "edit",
      "delete",
      "rename",
      "properties"
    ]
  },
  "ribbon": {
    "tabs": [
      {
        "name": "Home",
        "groups": [
          {
            "name": "Actions",
            "buttons": [
              {
                "name": "RunCheck",
                "label": "Run Quality Check",
                "icon": "Play"
              }
            ]
          }
        ]
      }
    ]
  },
  "assets": {
    "quality-rule-icon": "assets/quality-rule-medium.png"
  }
}
```

---

## Configuration Files

### Environment Files (.env.dev / .env.test / .env.prod)

```env
# Workload identity
WORKLOAD_NAME=Contoso.DataQuality

# Entra ID
AZURE_AD_APP_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_AD_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Fabric
FABRIC_WORKSPACE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
FABRIC_CAPACITY_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Dev Gateway (dev only)
DEV_GATEWAY_PORT=5000

# External backend (if any)
BACKEND_URL=https://your-backend.azurewebsites.net
```

### Template Processing

Manifest files support **template variables** that resolve from `.env.*` files at build time:

```json
{
  "name": "{{WORKLOAD_NAME}}",
  "backendUrl": "{{BACKEND_URL}}"
}
```

Build scripts (`BuildManifestPackage.ps1`) replace `{{VAR}}` with values from the active environment file.

---

## Build Output Structure

```
build/
├── Frontend/                  # Compiled React app (Vite output)
│   ├── index.html
│   ├── assets/
│   └── [bundled JS/CSS]
│
├── DevGateway/               # DevGateway config for local testing
│   ├── config.json
│   └── [gateway binaries reference]
│
└── Manifest/                 # NuGet package for deployment
    └── Contoso.DataQuality.1.0.0.nupkg
```

---

## Manifest Folder in Source

```
Manifest/
├── Product.json                          # Workload frontend config
├── WorkloadManifest.xml                  # Workload backend config
├── QualityRule/                          # One folder per item type
│   ├── QualityRuleItem.json              # Item frontend manifest
│   └── QualityRuleItem.xml               # Item backend manifest
├── QualityDashboard/                     # Another item type
│   ├── QualityDashboardItem.json
│   └── QualityDashboardItem.xml
└── assets/                               # Shared icon assets
    ├── workload-icon.png
    ├── quality-rule-small.png
    ├── quality-rule-medium.png
    ├── quality-rule-large.png
    ├── quality-dashboard-small.png
    ├── quality-dashboard-medium.png
    └── quality-dashboard-large.png
```

---

## Naming Conventions

| Element | Pattern | Example |
|---------|---------|---------|
| WorkloadName | `[Organization].[WorkloadName]` | `Contoso.DataQuality` |
| Dev WorkloadName | `Org.[WorkloadName]` | `Org.DataQuality` |
| Item type name | PascalCase, singular | `QualityRule` |
| Backend manifest | `[ItemName]Item.xml` | `QualityRuleItem.xml` |
| Frontend manifest | `[ItemName]Item.json` | `QualityRuleItem.json` |
| Item folder | `[ItemName]/` | `QualityRule/` |
| Asset files | kebab-case, ≤32 chars | `quality-rule-medium.png` |

---

## Validation Checklist

Before building the NuGet package, verify:

- [ ] `WorkloadManifest.xml` `<Name>` matches `Product.json` `"name"`
- [ ] Each item's XML `<Name>` matches its JSON `"name"`
- [ ] All icon paths in XML reference files that exist in `FE/assets/`
- [ ] All assets are ≤1.5 MB
- [ ] Total assets count ≤15
- [ ] Filenames ≤32 characters, alphanumeric + hyphens only
- [ ] Total item types ≤10
- [ ] `.env.*` variables all have values for the target environment
- [ ] Entra App ID in `WorkloadManifest.xml` matches `.env.*` `AZURE_AD_APP_ID`
- [ ] Editor paths in item JSON match actual React component routes
