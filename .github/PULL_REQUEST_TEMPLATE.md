<!--
Thanks for contributing. The single most useful thing you can put in this box is
the evidence: what you saw, where, and when. A one-line PR is fine if it has that.
Full guide: ../CONTRIBUTING.md
-->

## What changed, and what proves it

<!--
Example of a complete PR body:

  Observed on 2026-08-14: the SQL endpoint returned 404 for 2m40s after lakehouse
  creation, then 200. The fixed 2-minute sleep in lakehouse-agent was under it.
  Replaced with a poll, max 5 min.
-->



**Evidence level:** <!-- observed (seen in a real tenant, with a trace / response body / test output) | doc (Microsoft Learn or an announcement) -->

**Owning agent / brain:** <!-- e.g. Fabric-Brain / lakehouse-agent — routing table: ../AGENTS.md -->

---

## Both gates ran locally

```bash
cd Meta-Brain
python -m pytest tests/ -v --tb=short     # gate 1 — structure, links, clocks
cd ..
python Meta-Brain/tools/scan_public_safety.py .   # gate 2 — no client leak
```

- [ ] Gate 1 green — the count did not *drop* (a drop means assertions stopped being collected)
- [ ] Gate 2 prints `clean`

## The five rules that fail PRs

<!-- Detail for each: ../CONTRIBUTING.md#the-five-rules-that-fail-prs -->

- [ ] **1. Size** — every `instructions.md` I touched is still under 20 KB. Overflow went to a
      companion file, referenced from the load order at the top.
- [ ] **2. Labels** — nothing is marked **verified** without an artifact behind it. When unsure, I
      wrote `doc`.
- [ ] **3. Public by default** — company is Zava, GUIDs are visibly fake, no path contains an
      account name, no secret is committed. Including in the commit message.
- [ ] **4. Catalog matches disk** — if I added, renamed or removed an agent folder, I updated that
      brain's `agents/_catalog.yaml` in the same commit.
- [ ] **5. Dated claims** — any retirement or deprecation date I documented is registered in
      `Meta-Brain/clocks.yaml`.

## Scope

- [ ] I did not fork a base, a preset or an `instructions.md` to make a variant. I added an axis
      value, a module or a preset line instead.
- [ ] If this crosses an ownership boundary, I said so above: what was produced, which agent is
      next, which files and IDs are affected.

<!--
Screenshots: the scanner cannot read images — it only checks text. If you attach one,
you are the gate. See ../docs/proof/README.md before you add it.
-->
