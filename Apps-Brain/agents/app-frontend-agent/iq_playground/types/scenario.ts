export type ReportItem = {
  title: string;
  source: string;
  quote: string;
  note: string;
};

export type Report = {
  reasoningSteps: number;
  scanSummary: string;
  items: ReportItem[];
  verdictIntro: string;
  verdictList: string[];
};

export type ThinkingStep = {
  label: string;
  sub: string;
  /** How long this step stays on screen, in ms. Defaults to 1400. */
  durationMs?: number;
};

export type SourceSystem = "fabric" | "foundry" | "web" | "governance" | "email" | "teams" | "meeting";

/** Which Microsoft IQ layer a source belongs to, so the experience can surface *which* enterprise
 *  intelligence answered a given step rather than just naming the underlying system. */
export type IQLayer = "work" | "web" | "fabric" | "foundry" | "none";

export type SourceRef = {
  id: string;
  label: string;
  system: SourceSystem;
  detail: string;
};

export type ScenarioOption = {
  id: string;
  title: string;
  badge?: string;
  /** Short "supported by" line shown under the badge (e.g. crediting Fabric analytics as evidence). */
  supportedBy?: string;
  body: string;
  /** Reply the assistant gives when a non-recommended option is picked: it explains the risk
   *  and steers back. The cards stay selectable so the presenter can then pick the recommended one. */
  response?: string;
  responseSources?: SourceRef[];
};

export type PersonRef = {
  name: string;
  title: string;
  sub: string;
  location: string;
  initials: string;
  color: string;
  /** Object pronoun used in the send-email follow-up message (e.g. "him", "her", "them"). */
  pronoun?: string;
  /** Possessive pronoun used in the send-email follow-up message (e.g. "his", "her", "their"). */
  possessive?: string;
};

export type EmailDraft = {
  to: string;
  cc?: string;
  subject: string;
  bodyParagraphs: string[];
  /** Grounded reference chips shown below the email body (reuses the same source-citation system). */
  references?: SourceRef[];
};

export type Choice = {
  label: string;
  user: string;
  assistant: string;
  chain: string;
  mention?: string;
  report?: Report;
  thinkingSteps?: ThinkingStep[];
  /** Full markdown "reflection" the agent worked through before writing its final message (e.g. a
   *  competitor research brief) \u2014 rendered as a collapsible "Thinking" block above the assistant text. */
  reflection?: string;
  sources?: SourceRef[];
  /** When true, this turn has no user-typed message \u2014 it plays as a proactive system notification. */
  proactive?: boolean;
  /** When true (with proactive), this turn is not offered as a suggested-reply button \u2014 it can only be
   * triggered externally (e.g. by clicking a scenario card inside the previous message). */
  autoTriggerOnly?: boolean;
  /** When true, once this choice's message finishes revealing, automatically continue into the next
   * scene's proactive/autoTriggerOnly choice (chains consecutive system-notification steps together,
   * e.g. SAP operational validation \u2192 Compliance Agent governance review). */
  chainNext?: boolean;
  /** Scenario cards rendered in a horizontally scrolling carousel below the message text. */
  scenarios?: ScenarioOption[];
  /** Inline contact card for a person referenced in this turn (e.g. an approver). */
  person?: PersonRef;
  /** Email draft card rendered below the message text, with an interactive send action. */
  emailDraft?: EmailDraft;
  /** Short topic phrase used in the send-email follow-up confirmation (e.g. "the competitor campaign and the recommended response"). */
  followupTopic?: string;
  /** Governance authorization card (Compliance Agent) rendered below the message text. */
  authorization?: AuthorizationStatus;
  /** When set, selecting this choice opens a side modal instead of advancing the scripted conversation. */
  opensModal?: "approval-policy";
};

export type Scene = {
  choices: Choice[];
};

export type Message = {
  role: "user" | "assistant";
  text: string;
  chain?: string;
  mention?: string;
  report?: Report;
  reflection?: string;
  sources?: SourceRef[];
  scenarios?: ScenarioOption[];
  person?: PersonRef;
  emailDraft?: EmailDraft;
  authorization?: AuthorizationStatus;
};

/** Governance authorization snapshot shown by the Compliance Agent: it tells the user *why* they
 *  personally cannot execute the action themselves and who has to sign off. */
export type AuthorizationStatus = {
  role: string;
  approver: string;
  transferPercent: number;
  thresholdPercent: number;
  statusLabel: string;
};
/* ---------- Cowork session replay ----------
   A self-contained autonomous agent session: one prompt that the agent works through end to end
   with no clarifying questions, producing a deliverable. The replay shows collapsible reasoning
   blocks, tool-use status lines with substeps, generated images, a QA pass and the final artifact,
   while a sticky Tasks panel tracks the macro tasks to completion. This is independent from the
   conversation tracks and shares none of their state. */

export type CoworkTaskStatus = "pending" | "in_progress" | "done";

export type CoworkTask = { id: number; title: string };
export type CoworkEvent =
  | { kind: "thinking"; text: string; duration: number }
  | { kind: "step"; label: string; duration: number; substeps?: string[] }
  | { kind: "assistant"; text: string; duration: number }
  | { kind: "taskUpdate"; taskId: number; status: CoworkTaskStatus; duration: number }
  | { kind: "image"; file: string; caption: string; duration: number }
  | { kind: "slides"; count: number; qa: string; duration: number }
  | { kind: "deliverable"; file: string; slides: number; status: string; duration: number };

/* ---------- Scenario file ----------
   Everything below describes a complete business use case. The engine renders it and never
   hardcodes any of it, so adding a use case means adding a scenario file — not touching the
   engine. This mirrors schema/scenario.schema.json, which is the authoring contract. */

/** A specialist agent taking part in the scenario. Rendered in the "Pinned" sidebar. */
export type AgentRef = {
  name: string;
  /** One-line description of what the agent is responsible for. */
  sub: string;
  color: string;
  /** Which Microsoft IQ layer this agent draws on, when it maps to one. */
  iq?: IQLayer;
};

/** An entry in the Cowork "Upcoming" list. `action` names the track it launches, if any. */
export type UpcomingTask = {
  title: string;
  subtitle: string;
  action?: string;
};

export type TryThis = { label: string; color: string };

/** Chrome of the Copilot-style surface: everything in the shell that is scenario-specific. */
export type ShellConfig = {
  /** Past conversation titles listed under "Conversations" in the sidebar. */
  conversationHistory: string[];
  suggestedChips: string[];
  /** Short chip text that starts the scenario (the full prompt is still typed on click). */
  openerChip?: string;
  upcomingTasks: UpcomingTask[];
  tryThese: TryThis[];
};

/** One scripted path through the scenario. The user advances one scene per click. */
export type Track = {
  id: string;
  label: string;
  scenes: Scene[];
};

export type CoworkSession = {
  skillsUsed: string[];
  tasks: CoworkTask[];
  events: CoworkEvent[];
};

/** Scenario-specific artifacts the shell opens in side panels and modals. */
export type ScenarioArtifacts = {
  authorization?: AuthorizationStatus;
};

export type Persona = {
  role: string;
  goal?: string;
  /** Role of the human who signs off. Never a real name — {{approverName}} resolves at render time. */
  approverRole?: string;
};

export type Trigger = {
  kind: "competitive-signal" | "demand-shift" | "incident" | "planning-cycle" | "inbound-request";
  description: string;
  detectedBy?: IQLayer;
};

/** The mandatory human-in-the-loop checkpoint. A scenario where agents execute material business
 *  actions with no approval gate is not a story enterprises buy, so this is required. */
export type Governance = {
  approvalThreshold: string;
  policySource?: string;
  auditRetention?: string;
};

export type Scenario = {
  schemaVersion: 1;
  id: string;
  title: string;
  summary?: string;
  industry?: string;
  /** Marks a starter template made of placeholders rather than a real use case. */
  template?: boolean;
  persona: Persona;
  trigger?: Trigger;
  agents: AgentRef[];
  governance: Governance;
  shell: ShellConfig;
  tracks: Track[];
  coworkSession?: CoworkSession;
  artifacts?: ScenarioArtifacts;
};



