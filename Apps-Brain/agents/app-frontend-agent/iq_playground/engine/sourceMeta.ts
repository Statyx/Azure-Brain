import type { IQLayer, SourceSystem } from "../types/scenario";

/* Maps every grounded source a scripted step can cite to the agent that produced it and to the
   Microsoft IQ layer it belongs to. The `iq` field is what lets the experience show which layer of
   enterprise intelligence answered a step: Work IQ (M365 collaboration signals), Web IQ (external
   market signals), Fabric IQ (business data and forecasting) and Foundry IQ (agent grounding and
   retrieval). Sources that are plain systems of record or policy checks carry "none". */
export const sourceSystemMeta: Record<SourceSystem, { label: string; color: string; abbr: string; iq: IQLayer }> = {
  fabric: { label: "BI Analyst Agent", color: "#c23fa0", abbr: "B", iq: "fabric" },
  foundry: { label: "Marketing Agent", color: "#b5641f", abbr: "P", iq: "foundry" },
  web: { label: "Market Signal Agent", color: "#0f7a6c", abbr: "W", iq: "web" },
  governance: { label: "Compliance Agent", color: "#3b3b3b", abbr: "S", iq: "none" },
  email: { label: "Email", color: "#2e8fd6", abbr: "@", iq: "work" },
  teams: { label: "Teams", color: "#5b5fc7", abbr: "T", iq: "work" },
  meeting: { label: "Meeting", color: "#7b5cd6", abbr: "M", iq: "work" },
};

/** Display metadata for the four Microsoft IQ layers, used by the IQ trace panel. */
export const iqLayerMeta: Record<Exclude<IQLayer, "none">, { label: string; color: string; description: string }> = {
  work: {
    label: "Work IQ",
    color: "#2e8fd6",
    description: "Human context from Microsoft 365 — mail, Teams, documents and calendar.",
  },
  web: {
    label: "Web IQ",
    color: "#0f7a6c",
    description: "External market, competitor and public web signals.",
  },
  fabric: {
    label: "Fabric IQ",
    color: "#c23fa0",
    description: "Business data, ontology and forecasting from Microsoft Fabric.",
  },
  foundry: {
    label: "Foundry IQ",
    color: "#b5641f",
    description: "Agent grounding and knowledge retrieval from Azure AI Foundry.",
  },
};



