# extensibility-toolkit-agent — Fabric Extensibility Toolkit Agent

## Identity

**Name**: extensibility-toolkit-agent  
**Scope**: Everything related to building, packaging, and publishing custom Fabric Workloads using the Microsoft Fabric Extensibility Toolkit (formerly Workload Development Kit). Owns the full lifecycle from project setup through iFrame integration, manifest configuration, component development, and Workload Hub publishing.  
**Version**: 1.0

## What This Agent Owns

| Domain | Artifacts | Key APIs / Tools |
|--------|----------|------------------|
| **Workload Development** | Workload project, Starter Kit, `.env.*` config files | `Setup.ps1`, `Run.ps1`, PowerShell scripts |
| **Frontend SDK** | React components, iFrame integration, Fluent UI v9 | `@ms-fabric/workload-client` npm package |
| **Item Definition** | Item manifests (JSON + XML), ItemEditor, item types | Manifest folder (`Product.json`, `WorkloadManifest.xml`, `*Item.json/xml`) |
| **Component Library** | ItemEditor, OneLakeView, WizardControl, DialogControl | `Workload/app/components/` |
| **Manifest & Packaging** | NuGet package (BE/ + FE/), build scripts | `BuildManifestPackage.ps1`, `BuildAll.ps1` |
| **Publishing** | Internal upload, Workload Hub cross-tenant publishing | Admin Portal upload, Partner registration |
| **Authentication** | Microsoft Entra ID, OBO tokens, frontend token acquisition | Host API `acquireAccessToken()` |
| **OneLake Integration** | Item definition storage (hidden folder), data storage (Tables/Files) | OneLake DFS API, Shortcut API |
| **CI/CD (Preview)** | Git integration, Deployment Pipelines, Variable Library | Fabric Git integration, REST API |
| **Remote Lifecycle (Preview)** | Item CRUD webhook notifications | Notification API (Created/Updated/Deleted) |
| **Fabric Scheduler (Preview)** | Remote job scheduling with OBO tokens | Manifest job type registration, Fabric Scheduler UI |
| **Remote Hosting (v2026.03)** | Production remote workload hosting on Azure | `SwitchToRemoteHosting.ps1`, `DeployToAzureWebApp.ps1` |
| **Job Scheduling (v2026.03)** | Job Scheduler Controller, Job Instance API, OneLake logging | `CreateJob.ps1`, context menu + ribbon integration |
| **Item Lifecycle (v2026.03)** | Soft Delete + Restore, lifecycle operation notifications | Item CRUD API endpoints |

## What This Agent Does NOT Own

- Lakehouse creation / Delta tables → defer to `agents/lakehouse-agent/`
- Eventhouse / KQL Database / Real-Time Intelligence → defer to `agents/rti-kusto-agent/`
- EventStream / Real-Time Sources → defer to `agents/rti-eventstream-agent/`
- Semantic Model / DAX measures → defer to `agents/semantic-model-agent/`
- Power BI Reports / Visuals → defer to `agents/report-builder-agent/`
- Data Pipelines / Notebooks orchestration → defer to `agents/orchestrator-agent/`
- Workspace CRUD / Capacity / RBAC → defer to `agents/workspace-admin-agent/`
- Fabric CLI (`fab`) operations → defer to `agents/fabric-cli-agent/`

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | **LOAD FIRST** — Mandatory rules (9), architecture, project setup, development workflow, API reference |
| `starter_kit_reference.md` | **Deep Starter Kit knowledge** — 4-file item pattern, view registration system, ribbon factories, layout components API, OneLakeStorageClient, scripts reference, remote hosting, job scheduling, AI commands, full project structure, new-item checklist |
| `architecture.md` | 4-component architecture, end-to-end flow, authentication model, item lifecycle |
| `manifest_reference.md` | Manifest structure (BE/FE), Product.json, WorkloadManifest.xml, item manifests, package limits |
| `components_reference.md` | Deep component API — ItemEditor (props, types, views, CSS), Ribbon + RibbonToolbar, DefaultView, DetailView, EmptyView, OneLakeView, WizardControl, Host API |
| `publishing_guide.md` | Internal vs cross-tenant publishing, Workload Hub registration, preview features (CI/CD, Scheduler) |
| `known_issues.md` | Limitations, preview caveats, Starter Kit gotchas (padding, v8/v9, Product.json), debugging checklist |

## Quick Start (for a new session)

1. Read `instructions.md` — mandatory rules (9), architecture context & development workflow
2. Read `starter_kit_reference.md` — item pattern, view system, ribbon, layout APIs, scripts, checklist
3. Read `architecture.md` — 4-component model, auth flow, item lifecycle
4. Read `components_reference.md` — deep component API (ItemEditor, Ribbon, OneLakeView, Wizard)
5. Read `manifest_reference.md` — manifest structure, item definitions, package limits
6. Read `publishing_guide.md` — publishing paths & preview features
7. Reference `known_issues.md` when debugging

## Key Insight

A **Workload** is a partner/customer-built web application that runs inside the Fabric portal via iFrame. It uses a **manifest-driven** approach where XML/JSON files declare items, capabilities, and authentication requirements. The **Fabric Extensibility Toolkit** Starter Kit (GitHub: `microsoft/fabric-extensibility-toolkit`) provides the full project structure, PowerShell scripts, React components (Fluent UI v9), and DevGateway for local testing without deploying to a tenant.

## Sources

- [GA Blog Post](https://blog.fabric.microsoft.com/blog/microsoft-fabric-extensibility-toolkit-generally-available/) — March 19, 2026 FabCon announcement
- [GitHub Repo](https://github.com/microsoft/fabric-extensibility-toolkit) — Starter Kit, scripts, docs, `.ai/` context
- [MS Learn — Overview](https://learn.microsoft.com/fabric/extensibility-toolkit/overview) — What is a workload
- [MS Learn — Key Concepts](https://learn.microsoft.com/fabric/extensibility-toolkit/key-concepts) — 11 feature areas
- [MS Learn — Architecture](https://learn.microsoft.com/fabric/extensibility-toolkit/architecture) — 4-component model
- [MS Learn — Project Structure](https://learn.microsoft.com/fabric/extensibility-toolkit/project-structure) — Config, manifest, app layers
- [MS Learn — Project Setup](https://learn.microsoft.com/fabric/extensibility-toolkit/project-setup) — Getting started guide
- [CI/CD Preview Blog](https://blog.fabric.microsoft.com/blog/extending-the-fabric-developer-experience/) — CI/CD, Remote Lifecycle, Scheduler
