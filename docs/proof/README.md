# Proof shots — what to capture, and what must never be in frame

This folder holds the few screenshots that show the brain actually produced something. Four are
enough; a gallery is not the goal, credibility is.

---

## Rule zero: verify before `git add`, never after

**The leak scanner is blind to images.** `SCAN_SUFFIXES` in
`Meta-Brain/tools/scan_public_safety.py` covers `.md`, `.py`, `.json`, `.yaml`, `.ps1`, `.bicep` —
no image format. Gate 2 will pass a screenshot containing a tenant GUID, a customer name or a real
SQL endpoint without a word of complaint. This is stated in
[`PUBLIC_SAFETY.md`](../../PUBLIC_SAFETY.md) §5: *"Screenshots and GIFs checked by eye — the
scanner cannot read images."*

And a committed image **stays in the git history forever**. On a public repo that is being
promoted, a bad shot is not a mistake you fix with a follow-up commit — it needs a history rewrite,
after the content has already been cloned. So:

1. Take the shot.
2. Open the final PNG at 100 % and **read every string in it**.
3. Only then `git add`.
4. Commit the images **alone**, so a mistake caught before pushing is one `git reset` away.

---

## The universal checklist

| Check | Why |
| --- | --- |
| **Browser in full screen (F11), or crop the chrome entirely** | Kills the URL bar, the tabs and the profile picture in one move. The URL is where workspace and item GUIDs live. |
| Top-right avatar, name and tenant label cropped | Identifies you and the tenant. |
| No path containing an account name | `C:\Users\<you>\...` in a terminal prompt is the single most common leak. `cd` somewhere neutral first, or crop the prompt. |
| Workspace named `Zava - <something>` | A workspace named with your initials trips the `personal-workspace-prefix` rule — in text. In an image, nothing catches it but you. |
| No real `*.datawarehouse.fabric.microsoft.com` host | Real SQL endpoints are a flagged pattern. |
| No GUID that came from a real tenant | Even expired. Crop it or blur it. |
| Sample data is **Zava** data | No real customer name in a chart label, a table cell or a filter. |
| No token, no secret in a scrollback | Terminal shots especially. |
| Readable at 100 % on a phone | Most of the traffic will be mobile. Zoom the app to 110–125 % *before* capturing rather than scaling the PNG up afterwards. |

Identity slots to use: **Zava** · `zava.com` · `zava.onmicrosoft.com` · workspace prefix
`Zava - ` · resource group `rg-zava-<workload>`. Full table in
[`PUBLIC_SAFETY.md`](../../PUBLIC_SAFETY.md) §1.

---

## The four shots

Ordered by what they buy you. If you only do two, do 1 and 3.

### 1. `01-agent-loop.png` — the mechanism

**Proves:** an agent read an instruction file and then acted on it. This is the part nobody
understands from a description, and it is the whole pitch.

**Frame:** a terminal where Copilot reads
`Fabric-Brain/agents/lakehouse-agent/instructions.md`, then performs the action — ideally showing
the async pattern the brain insists on (HTTP 202, then the poll).

**Highest risk shot:** the prompt shows your working directory. Crop the prompt or run from a short
neutral path. Also scrub the scrollback for tokens.

### 2. `02-workspace-items.png` — it deploys real things

**Proves:** these are not suggestions, items exist in a workspace.

**Frame:** the Fabric workspace list showing several item types together — lakehouse, semantic
model, report, pipeline or eventhouse. The variety is the point.

**Crop:** URL bar, tenant label, avatar, and the capacity name if it carries anything real.

### 3. `03-report.png` — the recognisable end of the chain

**Proves:** the chain completes into something a business person would accept.

**Frame:** the deployed Power BI report, several visuals, page tabs visible so it reads as a real
report rather than one lucky chart.

**Crop:** URL, tenant, avatar. **And read the data**: every label, legend and filter value must be
Zava.

### 4. `04-foundry-trace.png` — the differentiator

**Proves:** the multi-agent claim, and it is the shot almost nobody else can produce.

**Frame:** a Foundry trace showing the supervisor calling sub-agents — the hops, the tool calls,
the timings. It backs the brain's own line that *a trace is the only place a multi-agent system is
legible*.

**Crop:** project and resource names unless they are Zava-prefixed, endpoint URLs, thread and run
IDs.

---

## Conventions

- PNG, max ~1600 px wide, under 500 KB each. Compress before committing.
- Names exactly as above — the root `README.md` will reference them by path.
- One commit for all four: `docs(brain): add proof shots`.

## Once the files are here

Add this to the root [`README.md`](../../README.md), right after the **What this is** section:

```markdown
## 📸 What it produces

| | |
| --- | --- |
| ![The loop](docs/proof/01-agent-loop.png) | **The loop.** An agent reads the instruction file, then acts on it — async-first, HTTP 202 then poll, because that is what the brain mandates. |
| ![Workspace](docs/proof/02-workspace-items.png) | **Real items.** Lakehouse, semantic model, report, pipeline — deployed, not described. |
| ![Report](docs/proof/03-report.png) | **The end of the chain.** A deployed Power BI report over Zava data. |
| ![Trace](docs/proof/04-foundry-trace.png) | **Why it did that.** A Foundry trace of a supervisor calling its sub-agents. |
```

Do not add that block before the images exist — a broken image on the front page of a repo people
are arriving at from a link is worse than no image at all.
