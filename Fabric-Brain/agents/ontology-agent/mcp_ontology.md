# MCP Ontology — Consume an Ontology as an MCP Server

> Source: [Use Ontology MCP Server — Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-use-ontology-mcp-server) (preview, last updated 2026-05).

## What it is

A deployed **Ontology (preview) item** can be exposed as an **MCP server**. Any MCP-capable client
(VS Code agent mode, Claude, etc.) can then discover and query the knowledge graph through the MCP
protocol — entity types, relationships, and graph traversal — without writing GQL by hand. This turns
the ontology into a live tool for an AI orchestrator.

> This is the **consumption / runtime** counterpart to the authoring this agent already owns. You still
> design + deploy the ontology (entity types, bindings, relationships, contextualizations) via the
> Fabric REST API; the MCP server is how an agent *talks to it* afterwards.

## Prerequisites

- **Paid F2+ Fabric capacity** (or P1+ Power BI Premium with Fabric enabled). Confirmed by Learn for the
  MCP-server path: "a paid F2 or higher Fabric capacity". (A separate Data Agent *bound to* an ontology
  source has no documented SKU floor — see `known_issues.md`; verify empirically.)
- **Ontology item (preview) enabled** on the Fabric tenant (Admin → tenant settings → "Ontology item (preview)").
- A **deployed ontology item** with entity types + relationships (an empty ontology exposes nothing useful).

## Forming the MCP server URL

1. Open the ontology item in Fabric. The browser URL is:
   `https://app.fabric.microsoft.com/groups/<workspace-ID>/ontologies/<ontology-item-ID>`
2. Copy `<workspace-ID>` and `<ontology-item-ID>`.
3. Build the MCP endpoint:
   ```
   https://api.fabric.microsoft.com/v1/mcp/dataPlane/workspaces/<workspace-ID>/items/<ontology-item-ID>/ontologyEndpoint
   ```

## Setup in VS Code

Create `.vscode/mcp.json` in the project folder:

```json
{
  "servers": {
    "fabric-ontology": {
      "type": "http",
      "url": "https://api.fabric.microsoft.com/v1/mcp/dataPlane/workspaces/<workspace-ID>/items/<ontology-item-ID>/ontologyEndpoint"
    }
  }
}
```

- VS Code shows an **Add Server** prompt → choose **HTTP** → paste the URL → name it → **Allow** + sign in (interactive auth with your Entra account).
- Or add it manually as above; VS Code authenticates on first start.
- Open **Chat (Ctrl+Shift+I)** → **agent mode** → start the server → it appears in the tool list.

> Auth is **interactive OAuth** against your Fabric identity (the same account that can open the ontology).
> There is no service-principal/API-key flow documented for the MCP endpoint in preview.

## When to use MCP vs the other consumption paths

| Goal | Use |
|------|-----|
| Let an AI agent explore/query the graph in natural language, live | **Ontology MCP server** (this file) |
| Hand-written GQL graph traversal queries | Graph Query Set / GQL (`graph_queries.md`) |
| Natural-language Q&A surfaced to end users in Fabric | Data Agent bound to the ontology (capacity floor unverified) |
| Time-series detail behind an entity | Eventhouse/KQL via `rti-kusto-agent` |

## Demo-project checklist (since you'll be showing this)

1. **Authoring** (this agent): deploy ontology — entity types, NonTimeSeries/TimeSeries bindings,
   relationships, contextualizations. Refresh the graph model.
2. **Verify** the graph is non-empty (at least one relationship resolves — empty graph = MCP returns nothing useful).
3. **Capacity**: ensure F2+ active for the MCP server (Learn-confirmed). Resume if paused:
   `az fabric capacity resume --capacity-name <name> --resource-group <rg>`.
4. **Tenant setting**: "Ontology item (preview)" must be ON for the tenant.
5. **`.vscode/mcp.json`** with the endpoint URL; start the server in agent mode; sign in.
6. **Warm-up**: ask one question before the demo (auth handshake + first query latency).

## Known limitations (preview)

- **Preview feature** — behaviour and URL shape may change; re-verify against the Learn doc.
- **Interactive auth only** — no documented SP flow for the MCP endpoint; the signed-in user must have access to the ontology.
- **Capacity gating** — MCP server needs F2+ (Learn-confirmed); the bound Data Agent path has no documented floor (verify empirically).
- An **empty/relationship-less ontology** exposes nothing meaningful — model the graph first.

## Cross-References

| Topic | File |
|-------|------|
| Deploy the ontology (entity types + bindings) | `entity_types_bindings.md` |
| Relationships + contextualizations (make the graph non-empty) | `relationships_contextualizations.md` |
| GQL hand-written queries (alternative to MCP) | `graph_queries.md` |
| Tenant settings + capacity gotchas | `known_issues.md` |
| KQL MCP tools (time-series behind entities) | `../rti-kusto-agent/mcp_kusto.md` |
