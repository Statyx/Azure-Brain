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

### Cropping is not always an option

Decide this *before* capturing, not after.

Cropping works when the sensitive thing is **peripheral** — a URL bar, an avatar, a shell prompt,
a run ID. Shots 1 and 4 are entirely in that category: full screen plus a cropped prompt covers
them.

Cropping fails when the sensitive thing **is the subject**. Shot 2 is the workspace list, so
masking a workspace name removes the very thing being shown — rename the workspace to `Zava - …`
instead, which takes seconds and requires re-running nothing. Shot 3's chart labels *are* the
visual; if the report sits on real data, no crop saves it and the demo has to be rebuilt on sample
data.

---

## What is in here

| File | Shows | Why it earns its place |
| --- | --- | --- |
| `01-agent-and-report.png` | A Data Agent answering a natural-language question, the DAX it generated, and the report beside it | The whole chain in one frame. Lead with it. |
| `02-instructions.png` | `lakehouse-agent/instructions.md` open in an editor | Explains the mechanism — an agent reads this, then acts |
| `03-ontology.png` | The Customer 360 ontology, 8 entities and 9 relations | The semantic layer the numbers sit on |
| `04-portal.png` | The operations portal landing page | The same artifacts served as an application |
| `social-card.png` | `01` under a scrim, with the title and the counts | The repo's social preview — the link card on LinkedIn, X, Slack |

`social-card.png` is generated, not captured: it composes `01-agent-and-report.png` at 1280 × 640,
the size GitHub expects under **Settings → General → Social preview**. Regenerate it rather than
editing it by hand, and re-upload it there if the counts change — nothing tests that the card and
the badges agree.

A Foundry trace of a supervisor calling its sub-agents is still missing. It is the one shot almost
nobody else can produce, and it would back the brain's own claim that *a trace is the only place a
multi-agent system is legible*. Crop project and resource names, endpoint URLs, thread and run IDs.

---

## What went wrong the first time

Five shots were uploaded through the GitHub web editor. One of them had to be pulled:

- The workspace was named with the author's **initials** followed by the project name, instead of
  the `Zava - ` prefix. This is the exact pattern the `personal-workspace-prefix` scanner rule
  exists to catch, and the scanner never saw it, because it was pixels.
- The item list underneath carried a **real 32-character tenant GUID**, repeated three times, as the
  auto-generated suffix on ontology child items (`ONT_..._graph_<guid>`).

Both gates were green while that image was live on a public repo. Two lessons, both now rules above:

1. **A leak in an image passes every automated check you have.** The only control is a human reading
   the picture before it is committed.
2. **Auto-generated item names carry GUIDs.** Ontology and graph child items append the workspace or
   item id to their display name, so a workspace item list is one of the most leak-prone screens in
   Fabric. Crop it, or capture the task flow view instead.

The image was only ever an `<img src>` pointing at GitHub's `user-attachments` CDN, so nothing
entered git history and no rewrite was needed. Had it been committed, it would have been permanent.

---

## Conventions

- PNG. Compress before committing; crop dead space rather than shipping a mostly-empty frame.
- Files live **in the repo**, under `docs/proof/`, referenced by relative path. Images pasted into
  the GitHub web editor land on the `user-attachments` CDN instead: they render on github.com but
  are absent from a clone, outside version control, and cannot be reviewed in a diff. For a repo
  whose whole instruction is *pin a tag and clone it*, that is the wrong place.
- Names carry their order — the root `README.md` references them by path.
