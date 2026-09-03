# Binding a Fabric data agent from code — the ARM / MCP path

> **Added 2026-09-03.** Companion to [`instructions.md`](instructions.md). Load it whenever the
> binding must be created **without a human in a browser** — CI, a demo deploy script, an
> environment promotion, or any unattended pipeline.
>
> This file does **not** replace the portal flow in `instructions.md` § *"the portal and the SDK
> are two halves of one flow"*. That flow is still correct and still the right choice when a
> person is present. This is the second path, and it is the one that survives automation.

---

## Why this file exists

The brain previously stated that a Fabric data agent has **no** MCP endpoint, and therefore that
the portal was the only way to create the connection. **That was false**, and it is retracted in
[`../../tenant_proofs.md`](../../tenant_proofs.md) and in [`known_issues.md`](known_issues.md).

The error is worth keeping in mind because of *how* it was made: the search that "proved" the
absence varied only the trailing segment of the URL (`…/dataagents/{id}/<16 different names>`)
and never varied the **path shape**. A negative result only ever covers the space you actually
searched.

---

## The route

```
POST https://api.fabric.microsoft.com/v1/mcp/workspaces/{workspaceId}/dataagents/{artifactId}/agent
Authorization: Bearer <token for https://api.fabric.microsoft.com>
Accept: application/json, text/event-stream
Content-Type: application/json
```

> ⚠️ **`Accept` must carry *both* media types.** Omit `text/event-stream` and the same URL
> answers `500` / `-32603`, which reads exactly like "this endpoint does not exist". That
> artefact is what produced the false absence proof.

There is **no single MCP route shape** in Fabric. Three families exist and none is derivable
from another — do not pattern-match one onto another:

| Target | Route |
|---|---|
| **Data agent** | `/v1/mcp/workspaces/{ws}/dataagents/{id}/agent` |
| Ontology | `/v1/mcp/dataPlane/workspaces/{ws}/items/{id}/ontologyEndpoint` |
| Semantic model | `/v1/mcp/fabricaihub/integrations/m365` |

---

## The ARM connection

```http
PUT https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}
    /providers/Microsoft.CognitiveServices/accounts/{account}
    /projects/{project}/connections/{connectionName}?api-version=2025-06-01
```

```json
{
  "properties": {
    "category": "RemoteTool",
    "group": "GenericProtocol",
    "authType": "ProjectManagedIdentity",
    "audience": "https://api.fabric.microsoft.com",
    "target": "https://api.fabric.microsoft.com/v1/mcp/workspaces/a0000000-0000-4000-a000-00000000000a/dataagents/a0000000-0000-4000-a000-00000000000b/agent",
    "isSharedToAll": false,
    "useWorkspaceManagedIdentity": false,
    "metadata": { "type": "fabric_iq_preview" }
  }
}
```

Four things in that body are load-bearing and none of them are obvious:

| Field | Why it matters |
|---|---|
| `metadata.type: "fabric_iq_preview"` | **undocumented.** Without it the connection is created but `FabricIQPreviewTool` will not resolve it. |
| `audience` | first-class property, **not** a metadata key. Omitting it produces an auth failure that names nothing. |
| `category: "RemoteTool"` | `AzureFabric` is **not** an ARM connection category — re-verified across five body shapes. That fact is real, and it never implied the goal was unreachable; it only ruled out one binding. |
| `group: "GenericProtocol"` | pairs with `RemoteTool`; the pair is what makes it an MCP server rather than a first-party connector. |

### `authType` — what ARM actually accepts

| Value | Result |
|---|---|
| `ProjectManagedIdentity` | ✅ works — **prefer this unattended** |
| `UserEntraToken` | ✅ works |
| `UserTokenAndProjectManagedIdentity` | ✅ accepted |
| `AgentUserImpersonation` | ✅ accepted |
| `AAD` | ❌ rejected at ARM validation |
| `AccountManagedIdentity` | ❌ rejected at ARM validation |

### Connection names — the charset rule is category-dependent

`RemoteTool` **rejects underscores**. `MicrosoftFabric` accepted them. Use dashes
(`zava-media-dataagent`), and do not assume a name that worked for one category is portable.

---

## The tool fires under a different name than you expect

| Tool class | Fires in the trace as | Connection it needs |
|---|---|---|
| `MicrosoftFabricPreviewTool` | the **connection** name | `CustomKeys` / `AzureFabric` — portal only |
| `FabricIQPreviewTool` | **`DataAgent_<data agent name>`** | `RemoteTool` / `GenericProtocol` — ARM |

`FabricIQPreviewTool` surfaces the **MCP server's own** tool name, not the connection's. A
verifier that asserts the connection name will report *"the tool never fired"* while the trace
plainly shows the call.

> **A stale assertion is indistinguishable from a broken chain.** When a check fails, confirm the
> check still describes the system before you go looking for the bug.

Set `require_approval="never"` on the tool, or an unattended run blocks forever waiting for an
approval nobody will give.

---

## Preflight — a paused capacity answers `404`

Do this **before** anything else, because the failure it prevents is the most misleading one in
this whole surface.

A paused Fabric capacity does not answer `503` or `409`. It answers:

```
HTTP 404
{"error":{"code":-32601,
          "message":"Internal error CapacityNotActive.Capacity <guid> is not active",
          "data":{"errorCode":"CapacityNotActive"}}}
```

The cause is **only in the body**, and Foundry relays the status while dropping the body — so it
reaches you as *"the remote MCP server returned HTTP 404 while enumerating tools"*, which reads
as a routing fault and sends you to inspect URLs and identities that were never wrong.

```bash
az resource show -g <rg> -n <capacity> \
   --resource-type Microsoft.Fabric/capacities --query properties.state -o tsv
az fabric capacity resume -g <rg> --capacity-name <capacity>
```

Send **one** `initialize` yourself at the start of any deploy or verify script and fail loudly
with the resume command in the message. It converts a multi-hour investigation into three
seconds.

After a resume, the first call can exceed Foundry's **100 s** tool timeout
(`TaskCanceledException … HttpClient.Timeout`). That is a cold start, not a second fault — retry
once before diagnosing.

Full write-up, plus the two general debugging habits it produced, in
[`../../../ERROR_RECOVERY.md`](../../../ERROR_RECOVERY.md) § 2.

---

## What travels over MCP, and what does not

The data agent's **own instructions do not travel**. The calling agent receives the answer, not
the guard rails that produced it. Any constraint you rely on — "always filter to the current
fiscal year", "never aggregate across brands" — must be **restated in the calling prompt**, even
though it is already written on the Fabric side.

This does not contradict the boundary rule in `instructions.md` § *"data semantics stay on the
data side"*: the *definition* stays in Fabric, the *reminder* travels in the prompt.

---

## Evidence

Proven on a live tenant 2026-09-03, unattended, 3/3 probes, **no portal step** — see
[`../../tenant_proofs.md`](../../tenant_proofs.md) § *"Foundry → Fabric data agent, unattended"*.

**What this does not settle:** nothing was measured on latency, cost, streaming behaviour, or
throughput. Both `FabricIQPreviewTool` and the A2A tool are **preview** surfaces; none of the
above is a GA contract.
