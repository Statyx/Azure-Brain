# RBAC Governance — Multi-Domain Security Patterns

## Purpose

Patterns for implementing Row-Level Security (RLS), Object-Level Security (OLS), and workspace role governance across multiple business domains in Fabric.

---

## Workspace Role Strategy

### Multi-Environment Model

```
{Domain}-Dev.Workspace     → Developers: Admin, Analysts: Contributor
{Domain}-Test.Workspace    → Developers: Contributor, Analysts: Viewer, QA: Contributor
{Domain}-Prod.Workspace    → Developers: Viewer, Analysts: Viewer, SPN: Contributor
```

### Role Assignment via API

```python
def assign_workspace_role(ws_id: str, principal_id: str, principal_type: str, role: str, headers: dict):
    """
    Assign a workspace role.
    principal_type: "User", "Group", "ServicePrincipal", "ServicePrincipalProfile"
    role: "Admin", "Member", "Contributor", "Viewer"
    """
    body = {
        "principal": {
            "id": principal_id,
            "type": principal_type
        },
        "role": role
    }
    
    resp = requests.post(
        f"{API}/workspaces/{ws_id}/roleAssignments",
        headers=headers,
        json=body
    )
    
    if resp.status_code == 409:
        # Already assigned — update instead
        resp = requests.put(
            f"{API}/workspaces/{ws_id}/roleAssignments/{principal_id}",
            headers=headers,
            json=body
        )
    
    return resp.status_code in (200, 201)
```

### Recommended Role Matrix

| Principal | Dev Workspace | Test Workspace | Prod Workspace |
|-----------|:------------:|:--------------:|:--------------:|
| Data Engineers (Group) | Admin | Contributor | Viewer |
| Analysts (Group) | Contributor | Viewer | Viewer |
| SPN (CI/CD) | Contributor | Contributor | Contributor |
| Business Users (Group) | — | Viewer | Viewer |
| Workspace Admin | Admin | Admin | Admin |

---

## Row-Level Security (RLS) Patterns

### Pattern 1: Simple Role-Based RLS

Filter data by a static role + security group mapping.

```dax
// In model.bim > roles[] section
{
    "name": "Europe Region",
    "modelPermission": "read",
    "tablePermissions": [
        {
            "name": "fact_sales",
            "filterExpression": "fact_sales[region] = \"Europe\""
        }
    ]
}
```

### Pattern 2: Dynamic RLS (UPN-Based)

Filter based on the logged-in user's email, matched against a security table.

**Step 1**: Create security mapping table in Lakehouse:

```csv
user_email,region,cost_center
alice@contoso.com,Europe,CC100
bob@contoso.com,Americas,CC200
carol@contoso.com,APAC,CC300
```

**Step 2**: Create DAX filter expression:

```dax
// Role: DynamicRLS
// Table: dim_security_mapping
// Filter:
dim_security_mapping[user_email] = USERPRINCIPALNAME()
```

**Step 3**: Create relationship: `dim_security_mapping[region]` → `fact_sales[region]`

> This way, each user only sees data for their assigned region.

### Pattern 3: Manager Hierarchy RLS

For scenarios where managers see their team's data + their own.

```dax
// Table: dim_employees
// Filter expression for DynamicManagerRLS role:
VAR _currentUser = USERPRINCIPALNAME()
VAR _userPath = 
    LOOKUPVALUE(dim_employees[hierarchy_path], dim_employees[email], _currentUser)
RETURN
    PATHCONTAINS(_userPath, dim_employees[employee_id])
```

### RLS in model.bim

```json
{
    "model": {
        "roles": [
            {
                "name": "DynamicRLS",
                "modelPermission": "read",
                "members": [],
                "tablePermissions": [
                    {
                        "name": "dim_security_mapping",
                        "filterExpression": "dim_security_mapping[user_email] = USERPRINCIPALNAME()"
                    }
                ]
            }
        ]
    }
}
```

### RLS Role Assignment via API

```python
def assign_rls_role(ws_id: str, model_id: str, role_name: str, members: list, headers: dict):
    """
    Assign users/groups to an RLS role in a semantic model.
    members: [{"identityType": "User", "identifier": "alice@contoso.com"}, ...]
    """
    # Use XMLA endpoint or Fabric API for role management
    body = {
        "roleName": role_name,
        "members": members
    }
    
    resp = requests.post(
        f"{API}/workspaces/{ws_id}/semanticModels/{model_id}/roles/{role_name}/members",
        headers=headers,
        json=body
    )
    return resp
```

---

## Object-Level Security (OLS)

Restrict access to specific columns or tables based on roles.

### Use Cases

- **HR domain**: Hide salary columns from non-HR users
- **Finance domain**: Hide detailed cost data from business users
- **Healthcare**: Hide PII (patient names, SSN) from analysts

### OLS in model.bim

```json
{
    "model": {
        "roles": [
            {
                "name": "RestrictedAnalyst",
                "modelPermission": "read",
                "tablePermissions": [
                    {
                        "name": "dim_employees",
                        "columnPermissions": [
                            {
                                "name": "salary",
                                "metadataPermission": "none"
                            },
                            {
                                "name": "ssn",
                                "metadataPermission": "none"
                            }
                        ]
                    }
                ]
            }
        ]
    }
}
```

> **`metadataPermission: "none"`** = Column is completely invisible to the user (not just filtered — it doesn't exist in their view).

---

## Multi-Domain Governance Model

### Domain Isolation Pattern

```
Tenant
├── Finance-Prod.Workspace
│   ├── LH_Finance.Lakehouse (RLS: cost_center)
│   ├── SM_Finance.SemanticModel (OLS: hides salary, bonus)
│   └── RPT_Finance.Report
│
├── Sales-Prod.Workspace
│   ├── LH_Sales.Lakehouse
│   ├── SM_Sales.SemanticModel (RLS: territory)
│   └── RPT_Sales.Report
│
├── HR-Prod.Workspace (Restricted)
│   ├── LH_HR.Lakehouse (RLS: department)
│   ├── SM_HR.SemanticModel (OLS: hides SSN, salary for non-HR)
│   └── RPT_HR.Report
│
└── Executive-Prod.Workspace
    ├── SM_Executive.SemanticModel (composite: links to all domains)
    └── RPT_Executive.Report (unrestricted for C-suite)
```

### Cross-Domain Data Sharing

Use **Lakehouse Shortcuts** to share data between domains without duplication:

```python
# Finance workspace reads from Sales Lakehouse via shortcut
# No data copy — just a pointer
shortcut_body = {
    "path": "Tables/fact_sales_summary",
    "target": {
        "oneLake": {
            "workspaceId": "<sales_workspace_id>",
            "itemId": "<sales_lakehouse_id>",
            "path": "Tables/fact_sales"
        }
    }
}
```

> **Security note**: Shortcuts inherit the source's security. The reader needs at least Viewer access to the source workspace.

---

## Cost Allocation / Chargeback

### Pattern: Tag Workspaces by Cost Center

```python
def set_workspace_description_with_cost_center(ws_id: str, cost_center: str, headers: dict):
    """
    Fabric doesn't support workspace tags natively.
    Use description field for cost tracking metadata.
    """
    body = {
        "description": f"Cost Center: {cost_center} | Domain: Finance | Owner: finance-team@contoso.com"
    }
    resp = requests.patch(f"{API}/workspaces/{ws_id}", headers=headers, json=body)
    return resp
```

### CU Allocation by Workspace

```kql
// KQL query for monitoring capacity consumption by workspace
// (requires Monitoring workspace / Admin monitoring enabled)
FabricEvents
| where EventType == "WorkloadMetrics"
| summarize TotalCU = sum(CUConsumed) by WorkspaceName, bin(Timestamp, 1d)
| order by TotalCU desc
```

### Chargeback Report Template

| Workspace | Domain | Cost Center | Monthly CU | % of Capacity | Monthly Cost |
|-----------|--------|-------------|-----------|---------------|-------------|
| Finance-Prod | Finance | CC100 | 12,000 | 35% | $728 |
| Sales-Prod | Sales | CC200 | 8,500 | 25% | $520 |
| HR-Prod | HR | CC300 | 4,000 | 12% | $250 |
| Executive | Exec | CC001 | 2,000 | 6% | $125 |
| Shared / Overhead | Platform | CC999 | 7,500 | 22% | $457 |
| **Total** | | | **34,000** | **100%** | **$2,080** |

---

## Audit & Compliance

### Track Role Changes

```python
def audit_role_assignments(ws_id: str, headers: dict) -> list:
    """Get current role assignments for compliance audit."""
    resp = requests.get(f"{API}/workspaces/{ws_id}/roleAssignments", headers=headers)
    assignments = resp.json().get("value", [])
    
    report = []
    for a in assignments:
        report.append({
            "workspace": ws_id,
            "principal_name": a["principal"].get("displayName", "Unknown"),
            "principal_type": a["principal"]["type"],
            "role": a["role"],
            "timestamp": a.get("createdDateTime", "Unknown")
        })
    
    return report
```

### Compliance Checklist

- [ ] All production workspaces have RBAC configured (no default access)
- [ ] Service Principals use Contributor role (not Admin)
- [ ] RLS is configured on all semantic models with PII or restricted data
- [ ] OLS hides sensitive columns (salary, SSN, health data), not just filter them
- [ ] Workspace descriptions include cost center and owner
- [ ] Role assignments reviewed quarterly
- [ ] Audit logs exported to Azure Log Analytics monthly
