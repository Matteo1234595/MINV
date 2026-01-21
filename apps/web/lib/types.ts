export type HealthSnapshot = {
  organization_id: string;
  score: number;
  components: Record<string, { value: number | null; score: number }>;
  computed_at: string;
};

export type KpiSnapshot = {
  organization_id: string;
  snapshot_at: string;
  metrics: Record<string, number>;
};

export type Insight = {
  id: string;
  title: string;
  body: string;
  severity: "info" | "medium" | "high";
  created_at: string;
};

export type InsightResponse = {
  organization_id: string;
  insights: Insight[];
};

export type ActionItem = {
  id: string;
  title: string;
  status: "open" | "done";
  due_at: string | null;
  created_at: string;
};

export type ActionResponse = {
  organization_id: string;
  actions: ActionItem[];
};

export type CopilotResponse = {
  content: string;
  model: string;
  tool_calls: Record<string, unknown>[];
};
