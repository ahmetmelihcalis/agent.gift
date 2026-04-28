export type StreamStatus = "idle" | "streaming" | "success" | "error";

export type StreamLog = {
  agent: string;
  role?: string;
  agent_id?: string;
  message: string;
};

export type AgentState = {
  id: string;
  name: string;
  role: string;
  specialty: string;
  status: "idle" | "working" | "done";
  headline: string;
  latest_note?: string | null;
};

export type ProductCard = {
  name: string;
  why_it_matches: string;
  price_label: string;
  url: string;
  source: string;
  editorial_note: string;
  matched_signals: string[];
  caveats: string[];
  comparison_note: string;
};

export type InvestigatePayload = {
  brief: string;
  budget?: string;
  region?: string;
  refine_instruction?: string;
};

export type InvestigationResult = {
  session_id: string;
  profile_summary: string;
  editorial_intro: string;
  markdown: string;
  tone_mode: string;
  applied_filters: Record<string, string | string[]>;
  profile_snapshot: {
    inferred_persona: string;
    obsessions: string[];
    aversions: string[];
    hidden_hooks: string[];
    gifting_risks: string[];
    tone_notes: string;
  };
  agents: AgentState[];
  products: ProductCard[];
};

type StreamEventMap = {
  status: { status: string; message: string };
  log: StreamLog;
  agents: { agents: AgentState[] };
  result: InvestigationResult;
  error: { message: string; detail?: string };
};

export type StreamEvent = {
  [K in keyof StreamEventMap]: {
    event: K;
    data: StreamEventMap[K];
  };
}[keyof StreamEventMap];
