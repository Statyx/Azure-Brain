import type { Scenario } from "../types/scenario";

/* The narrative rules. They live here, not in the build script, because they are needed in two
 * places: the CI gate and the in-browser loader. A scenario can be structurally valid and still be
 * a bad demo — this is the half of validation a JSON Schema cannot express. */

type Rule = { name: string; check: (s: Scenario) => string[] };

/* Real names that must never appear in a scenario (colleagues, customers, the presenter).
 * Fill it per demo, lower-case; keep it out of version control if the names are sensitive. */
export const REAL_NAME_DENYLIST: string[] = [];

export const narrativeRules: Rule[] = [
  {
    name: "at least three IQ layers are exercised",
    check: (s) => {
      const layers = new Set((s.agents ?? []).map((a) => a.iq).filter((iq) => iq && iq !== "none"));
      if (s.trigger?.detectedBy && s.trigger.detectedBy !== "none") layers.add(s.trigger.detectedBy);
      return layers.size >= 3
        ? []
        : [
            `only ${layers.size} IQ layer(s) used (${[...layers].join(", ") || "none"}). A scenario that leans on one layer does not make the Microsoft IQ argument.`,
          ];
    },
  },
  {
    name: "every decision offers a real choice",
    check: (s) => {
      const problems: string[] = [];
      for (const track of s.tracks ?? []) {
        track.scenes.forEach((scene, i) => {
          for (const choice of scene.choices) {
            if (!choice.scenarios) continue;
            if (choice.scenarios.length < 3) {
              problems.push(
                `${track.id} scene ${i}: ${choice.scenarios.length} option(s) offered; at least 3 are needed or the user is just watching a happy path.`
              );
            }
            const recommended = choice.scenarios.filter((o) => /recommended/i.test(o.badge ?? ""));
            if (recommended.length !== 1) {
              problems.push(
                `${track.id} scene ${i}: ${recommended.length} options badged "Recommended"; exactly 1 is required.`
              );
            }
          }
        });
      }
      return problems;
    },
  },
  {
    name: "agent claims are grounded",
    check: (s) => {
      const problems: string[] = [];
      for (const track of s.tracks ?? []) {
        track.scenes.forEach((scene, i) => {
          for (const choice of scene.choices) {
            if (/\d/.test(choice.assistant ?? "") && !(choice.sources?.length ?? 0)) {
              problems.push(
                `${track.id} scene ${i} ("${(choice.label || choice.user || "").slice(0, 40)}"): the reply quotes figures but carries no sources.`
              );
            }
            for (const option of choice.scenarios ?? []) {
              if (/\d/.test(option.response ?? "") && !(option.responseSources?.length ?? 0)) {
                problems.push(
                  `${track.id} scene ${i} option "${option.id}": the response quotes figures but carries no sources.`
                );
              }
            }
          }
        });
      }
      return problems;
    },
  },
  {
    name: "a human approval checkpoint exists",
    check: (s) =>
      s.governance?.approvalThreshold?.trim()
        ? []
        : [
            "governance.approvalThreshold is empty. Agents executing material actions unsupervised is not a story enterprises buy.",
          ],
  },
  {
    name: "no real person is named",
    check: (s) => {
      if (REAL_NAME_DENYLIST.length === 0) return [];
      const escaped = REAL_NAME_DENYLIST.map((n) => n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
      const hit = JSON.stringify(s).match(new RegExp(`\\b(${escaped.join("|")})\\b`, "i"));
      return hit
        ? [`the scenario names a real person ("${hit[0]}"). Use {{tokens}} resolved from the demo profile instead.`]
        : [];
    },
  },
  {
    name: "upcoming-task actions point at real tracks",
    check: (s) => {
      const ids = new Set((s.tracks ?? []).map((t) => t.id));
      return (s.shell?.upcomingTasks ?? [])
        .filter((t) => t.action && !ids.has(t.action))
        .map((t) => `upcoming task "${t.title}" launches track "${t.action}", which does not exist.`);
    },
  },
];

/** Structural checks. The CI gate uses the full JSON Schema; this is the subset the browser needs
 *  to fail a pasted file with a useful message instead of a blank screen. */
function checkShape(value: unknown): string[] {
  const problems: string[] = [];
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return ["the file is not a JSON object."];
  }
  const s = value as Partial<Scenario>;
  if (s.schemaVersion !== 1) problems.push('schemaVersion must be 1.');
  for (const field of ["id", "title"] as const) {
    if (typeof s[field] !== "string" || !s[field]) problems.push(`${field} is required.`);
  }
  if (!s.persona?.role) problems.push("persona.role is required.");
  if (!Array.isArray(s.agents) || s.agents.length === 0) problems.push("agents must list at least one agent.");
  if (!s.shell) problems.push("shell is required (conversation history, chips, Cowork entries).");
  if (!Array.isArray(s.tracks) || s.tracks.length === 0) {
    problems.push("tracks must contain at least one track.");
  } else {
    s.tracks.forEach((t, i) => {
      if (!t?.id) problems.push(`tracks[${i}].id is required.`);
      if (!Array.isArray(t?.scenes) || t.scenes.length === 0) {
        problems.push(`tracks[${i}] has no scenes.`);
      } else {
        t.scenes.forEach((scene, j) => {
          if (!Array.isArray(scene?.choices) || scene.choices.length === 0) {
            problems.push(`tracks[${i}].scenes[${j}] has no choices.`);
          }
        });
      }
    });
  }
  return problems;
}

/** Returns every problem found, prefixed by the rule that found it. Empty means the scenario is
 *  safe to play. Shape problems short-circuit the narrative rules, which assume a valid shape. */
export function validateScenario(value: unknown): string[] {
  const shape = checkShape(value);
  if (shape.length) return shape;
  const scenario = value as Scenario;
  return narrativeRules.flatMap((rule) => rule.check(scenario).map((p) => `${rule.name}: ${p}`));
}
