# foundry-orchestration-agent

Supervisor / multi-agent orchestration in Microsoft Foundry.

**Owns:** who calls whom at runtime — sub-agent delegation via **A2A**, capability attachment
via **toolbox** and direct tools, the identity model across the hop, and the guard-rails that
stop a supervisor looping.

**Does not own:** creating the agents themselves (`foundry-agent-service-agent`), the project
and its models (`foundry-project-agent`), the Fabric leg's specifics
(`foundry-fabric-bridge-agent`), or anything inside Fabric (`Fabric-Brain`).

## Read before use

- [`../../generation_map.md`](../../generation_map.md) — two Foundry generations coexist and
  **three** separate retirement clocks are running. Getting this wrong means writing code
  against a dying API.
- [`../../orchestration_patterns.md`](../../orchestration_patterns.md) — why A2A + toolbox,
  and what was ruled out.

## The three things people get wrong

1. **Connected Agents don't exist here.** `agent.as_tool` and Connected Agents are classic-only.
   Delegation is A2A.
2. **Creating a sub-agent doesn't expose it.** Incoming A2A must be enabled with an explicit
   PATCH — and the portal cannot do it.
3. **The A2A version defaults to v0.3.** Ask for v1.0 or you silently get the old protocol.

## Status

Written from Microsoft Learn documentation, **doc set checked 2026-08-04**.
Nothing in it has been executed against a tenant — see the verification checklist at the end of
[`instructions.md`](instructions.md) and log every real outcome in
[`known_issues.md`](known_issues.md).
