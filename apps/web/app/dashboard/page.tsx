"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "../../lib/api";

type HealthResponse = {
  organization_id: string;
  score: number;
  components: Record<string, { value: number | null; score: number }>;
  computed_at: string;
};

type KpiLatestResponse = {
  organization_id: string;
  snapshot_at: string;
  metrics: Record<string, number>;
};

type InsightApi = {
  id: string;
  title: string;
  body: string;
  severity: "info" | "medium" | "high";
  created_at: string;
};

type InsightsResponse = {
  organization_id: string;
  insights: InsightApi[];
};

const severityStyles: Record<"low" | "medium" | "high", string> = {
  low: "bg-slate-800 text-slate-200",
  medium: "bg-amber-500/20 text-amber-200",
  high: "bg-rose-500/20 text-rose-200"
};

export default function DashboardPage() {
  const [organizationId, setOrganizationId] = useState("");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [kpis, setKpis] = useState<KpiLatestResponse | null>(null);
  const [insights, setInsights] = useState<InsightApi[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    if (!organizationId) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const [healthResponse, kpiResponse, insightResponse] = await Promise.all([
        apiFetch<HealthResponse>(`/health/latest?organization_id=${organizationId}`),
        apiFetch<KpiLatestResponse>(`/kpis/latest?organization_id=${organizationId}`),
        apiFetch<InsightsResponse>(`/insights/latest?organization_id=${organizationId}`)
      ]);
      setHealth(healthResponse);
      setKpis(kpiResponse);
      setInsights(insightResponse.insights);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load dashboard data.");
    } finally {
      setIsLoading(false);
    }
  }, [organizationId]);

  useEffect(() => {
    if (organizationId) {
      loadDashboard();
    }
  }, [organizationId, loadDashboard]);

  const handleRecompute = async () => {
    if (!organizationId) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await apiFetch(
        `/insights/recompute?organization_id=${organizationId}`,
        { method: "POST" }
      );
      await loadDashboard();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to recompute insights.");
      setIsLoading(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-6 py-16">
      <section className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-400">
              AION Dashboard
            </p>
            <h1 className="text-3xl font-semibold text-white">Organization Pulse</h1>
          </div>
          <button
            type="button"
            onClick={handleRecompute}
            disabled={!organizationId || isLoading}
            className="inline-flex items-center justify-center rounded-full border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition hover:border-slate-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Recompute
          </button>
        </div>
        <label className="flex flex-col gap-2 text-sm text-slate-300">
          Organization ID
          <input
            value={organizationId}
            onChange={(event) => setOrganizationId(event.target.value)}
            placeholder="UUID"
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white placeholder:text-slate-500"
          />
        </label>
        {error && (
          <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 p-3 text-sm text-rose-200">
            {error}
          </div>
        )}
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Health score</p>
          <div className="mt-4 flex items-end gap-3">
            <span className="text-5xl font-semibold text-white">
              {health ? health.score : "--"}
            </span>
            <span className="text-sm text-slate-400">/ 100</span>
          </div>
          <p className="mt-3 text-sm text-slate-300">
            {health ? `Computed at ${new Date(health.computed_at).toLocaleString()}` : "No data yet."}
          </p>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Latest KPIs</p>
          <p className="mt-2 text-sm text-slate-300">
            {kpis ? `Snapshot ${new Date(kpis.snapshot_at).toLocaleDateString()}` : "No KPIs available."}
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {kpis &&
              Object.entries(kpis.metrics).map(([metric, value]) => (
                <div key={metric} className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
                    {metric.replace(/_/g, " ")}
                  </p>
                  <p className="mt-2 text-lg font-semibold text-white">{value.toFixed(2)}</p>
                </div>
              ))}
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <div className="flex items-center justify-between">
          <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Insights</p>
          {isLoading && <span className="text-xs text-slate-400">Refreshing...</span>}
        </div>
        <div className="mt-4 space-y-4">
          {insights.length > 0 ? (
            insights.map((insight) => {
              const severity =
                insight.severity === "info" ? "low" : insight.severity;
              return (
              <div key={insight.id} className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
                <div className="flex flex-wrap items-center gap-3">
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${severityStyles[severity]}`}>
                    {severity.toUpperCase()}
                  </span>
                  <h3 className="text-base font-semibold text-white">{insight.title}</h3>
                </div>
                <p className="mt-2 text-sm text-slate-300">{insight.body}</p>
                <p className="mt-2 text-xs text-slate-500">
                  {new Date(insight.created_at).toLocaleString()}
                </p>
              </div>
              );
            })
          ) : (
            <p className="text-sm text-slate-300">
              {organizationId ? "No insights available." : "Enter an organization ID to view insights."}
            </p>
          )}
        </div>
      </section>
    </main>
  );
}
