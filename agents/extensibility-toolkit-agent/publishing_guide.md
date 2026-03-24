# Publishing Guide — Fabric Extensibility Toolkit

## Publishing Paths

There are two paths to distribute a Fabric workload:

```
Build NuGet Package
       │
       ├── Internal Publishing (Org-only)
       │   └── Upload to Admin Portal → Configure tenant
       │
       └── Cross-Tenant Publishing (Workload Hub)
           └── Register → Submit → Preview → GA in marketplace
```

---

## Internal Publishing (Organization-Scoped)

For workloads used **only within your organization**.

### Steps

1. **Build the NuGet package**:
   ```powershell
   ./scripts/BuildManifestPackage.ps1
   # Output: build/Manifest/[WorkloadName].nupkg
   ```

2. **Upload to Fabric Admin Portal**:
   - Navigate to **Fabric Admin Portal** → **Workload Publishing**
   - Click **Upload workload**
   - Select the `.nupkg` file
   - Wait for validation and deployment

3. **Configure tenant settings**:
   - **Admin Portal** → **Tenant Settings** → **Workload Publishing**
   - Enable **"Users can use workloads published by the organization"**
   - Scope to specific security groups or entire organization

4. **Verify deployment**:
   - Open Fabric portal → any workspace → **New**
   - Your workload item types should appear under the workload category
   - Or navigate to: `app.fabric.microsoft.com/workloadhub/detail/<WORKLOAD_NAME>`

### Update Cycle

To update an internal workload:
1. Increment version in `WorkloadManifest.xml` and `Product.json`
2. Rebuild NuGet package
3. Upload new version to Admin Portal (replaces existing)

---

## Cross-Tenant Publishing (Workload Hub)

For ISVs and solution builders who want to distribute workloads to **any Fabric tenant** via the Workload Hub marketplace.

### Prerequisites

- A published workload must have a **globally unique ID**: `[Publisher].[Workload]`
- You must be a registered publisher
- The workload must meet Fabric certification requirements

### Steps

1. **Register as a publisher**:
   - Go to `https://aka.ms/fabric_workload_registration`
   - Complete the registration form
   - Provide publisher name, contact info, and workload details

2. **Set globally unique WorkloadName**:
   ```xml
   <!-- WorkloadManifest.xml -->
   <Name>Contoso.DataQuality</Name>
   ```
   - Use your registered publisher name as the prefix
   - This ID is permanent once published

3. **Submit publishing request**:
   - Through the registration portal
   - Provide workload NuGet package
   - Provide documentation, support info, pricing details

4. **Preview phase**:
   - Workload appears in Workload Hub as **Preview**
   - Limited visibility for testing and early adoption
   - Collect feedback and iterate

5. **GA phase**:
   - After successful Preview period
   - Workload becomes generally available in Workload Hub
   - All Fabric tenants can discover and install

### End-User Experience

End users discover workloads via:
- **Workload Hub** in Fabric portal (browse and search)
- Direct link: `app.fabric.microsoft.com/workloadhub/detail/<WORKLOAD_NAME>`
- Tenant admin can pre-approve specific workloads

---

## Preview Features

### CI/CD Support (Preview)

Workload items automatically participate in Fabric CI/CD when the workspace is Git-connected.

#### Git Integration

```
Workspace Item                    Git Repository
┌───────────────────┐            ┌───────────────────┐
│ MyItem.QualityRule │  ◄──sync──►  │ MyItem.QualityRule/│
│                   │            │   ├── .platform     │
│                   │            │   └── definition.json│
└───────────────────┘            └───────────────────┘
```

- Items serialize to `.platform` (Fabric metadata) + `definition.json` (item content)
- Standard Git operations: commit, branch, merge, pull request
- **No custom logic needed** — Fabric handles serialization automatically

#### Deployment Pipelines

```
Dev Workspace  ──►  Test Workspace  ──►  Prod Workspace
    (Git)              (Deploy)              (Deploy)
```

- Items move through stages (dev → test → prod)
- Optional deployment hooks for pre/post processing
- REST API compatible for CI/CD automation

#### Variable Library

Store environment-specific configuration as named variables:

```
Variable: "StorageConnectionString"
├── Dev:  "connection-string-dev"
├── Test: "connection-string-test"  
└── Prod: "connection-string-prod"
```

- Use variable names in item definitions instead of hard-coded values
- Variables resolve per environment at deployment time
- Avoids manual config changes during promotion

---

### Remote Lifecycle Notification API (Preview)

Opt-in webhook that notifies your backend when workload items are created, updated, or deleted.

#### Registration (WorkloadManifest.xml)

```xml
<NotificationEndpoint>
  <Url>https://your-backend.azurewebsites.net/api/fabric/notifications</Url>
  <Events>
    <Event>Created</Event>
    <Event>Updated</Event>  
    <Event>Deleted</Event>
  </Events>
</NotificationEndpoint>
```

#### Webhook Payload

```json
{
  "eventType": "Created",
  "workloadName": "Contoso.DataQuality",
  "itemType": "QualityRule",
  "itemId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "workspaceId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "timestamp": "2026-03-19T10:30:00Z"
}
```

#### Use Cases

| Scenario | Event | Action |
|----------|-------|--------|
| **License management** | Created | Check license quota, provision seat |
| **Infrastructure provisioning** | Created | Spin up backend resources for item |
| **External system sync** | Updated | Sync config changes to external system |
| **Cleanup** | Deleted | Tear down backend resources, release license |
| **CI/CD pipeline promotion** | Created (in target workspace) | Initialize item in new environment |

#### CI/CD Integration

When items are promoted via Deployment Pipelines:
- Target workspace receives `Created` events for new items
- Target workspace receives `Updated` events for existing items
- Each workspace gets its own notifications — supports per-environment backend provisioning

---

### Fabric Scheduler / Remote Jobs (Preview)

Enable scheduled job execution for workload items using Fabric's built-in scheduling infrastructure.

#### Registration (WorkloadManifest.xml)

```xml
<Jobs>
  <JobType>
    <Name>DataQualityCheck</Name>
    <DisplayName>Data Quality Check</DisplayName>
    <Description>Run quality checks on configured data sources</Description>
  </JobType>
  <JobType>
    <Name>DataQualityReport</Name>
    <DisplayName>Generate Quality Report</DisplayName>
  </JobType>
</Jobs>
```

#### Item Support (ItemManifest.xml)

```xml
<SupportedJobTypes>
  <JobType>DataQualityCheck</JobType>
  <JobType>DataQualityReport</JobType>
</SupportedJobTypes>
```

#### Scheduling Flow

```
1. User opens item in Fabric → Schedule tab appears automatically
2. User configures schedule (daily, weekly, cron-like)
3. At scheduled time, Fabric sends signed request to your backend:
   - Item context (workspaceId, itemId, itemType)
   - OBO token (on behalf of the scheduling user)
   - Job metadata (jobId, jobType, scheduledTime)
4. Your backend processes the job
5. Your backend reports status back to Fabric
6. Results appear in Fabric Monitoring Hub / Job History
```

#### Backend Request Handler

```
POST https://your-backend.azurewebsites.net/api/fabric/jobs

Headers:
  Authorization: Bearer <signed-request-token>

Body:
{
  "jobType": "DataQualityCheck",
  "jobId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "workloadName": "Contoso.DataQuality",
  "itemType": "QualityRule",
  "itemId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "workspaceId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "oboToken": "<on-behalf-of-token>",
  "scheduledTime": "2026-03-19T10:30:00Z"
}
```

#### What Jobs Can Do

With the OBO token, scheduled jobs can:
- Read/write OneLake (DFS API)
- Call Fabric REST APIs
- Call external APIs (any Entra-protected service)
- Access Spark Livy API
- Process data and store results

#### Job Status Reporting

```
POST https://api.fabric.microsoft.com/v1/workloads/{workloadName}/jobs/{jobId}/status

Body:
{
  "status": "Completed",  // "InProgress", "Completed", "Failed", "Cancelled"
  "message": "Quality check passed: 99.8% pass rate",
  "startTime": "2026-03-19T10:30:00Z",
  "endTime": "2026-03-19T10:31:45Z"
}
```

---

## Publishing Checklist

### Before Internal Publishing

- [ ] All manifest files validated (XML + JSON match)
- [ ] All icons present and ≤1.5 MB
- [ ] Package size ≤20 MB
- [ ] All item types have working ItemEditors
- [ ] Authentication tested with Entra app
- [ ] DevGateway testing passed
- [ ] Admin Portal tenant settings configured

### Before Workload Hub Publishing

- [ ] All internal publishing checks pass
- [ ] Globally unique WorkloadName (`[Publisher].[Workload]`)
- [ ] Publisher registration completed at `aka.ms/fabric_workload_registration`
- [ ] End-user documentation prepared
- [ ] Support contact information provided
- [ ] Pricing/licensing model defined (if applicable)
- [ ] Accessibility compliance verified (WCAG 2.1 AA)
- [ ] Performance tested under load
- [ ] Security review completed (no credential leaks, proper token handling)
