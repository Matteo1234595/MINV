"use client";

import { FormEvent, useCallback, useMemo, useState } from "react";

import { apiFetch, clearToken, getToken, setToken } from "../../lib/api";
import type {
  ActionItem,
  ActionResponse,
  CopilotResponse,
  HealthSnapshot,
  Insight,
  InsightResponse,
  KpiSnapshot
} from "../../lib/types";

const DEMO_ORG_ID = "00000000-0000-0000-0000-000000000000";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { apiFetch, clearTokens, getTokens, setTokens } from "../../lib/api";
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

type ActionItem = {
  id: string;
  title: string;
  status: string;
  due_at: string | null;
};

type ActionsResponse = {
  organization_id: string;
  actions: ActionItem[];
};

const severityStyles: Record<"low" | "medium" | "high", string> = {
  low: "bg-slate-800 text-slate-200",
  medium: "bg-amber-500/20 text-amber-200",
  high: "bg-rose-500/20 text-rose-200"
};

export default function DashboardPage() {
  const [organizationId, setOrganizationId] = useState(DEMO_ORG_ID);
  const [health, setHealth] = useState<HealthSnapshot | null>(null);
  const [kpis, setKpis] = useState<KpiSnapshot | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [copilotMessage, setCopilotMessage] = useState("");
  const [copilotResponse, setCopilotResponse] = useState<string | null>(null);
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tokenInput, setTokenInput] = useState("");

  const isAuthenticated = Boolean(getToken());

  const loadData = useCallback(async () => {
    if (!organizationId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [healthData, kpiData, insightsData, actionsData] = await Promise.all([
        apiFetch<HealthSnapshot>(`/health/latest?organization_id=${organizationId}`),
        apiFetch<KpiSnapshot>(`/kpis/latest?organization_id=${organizationId}`),
        apiFetch<InsightResponse>(`/insights/latest?organization_id=${organizationId}&limit=20`),
        apiFetch<ActionResponse>(`/actions/open?organization_id=${organizationId}`)
      ]);
      setHealth(healthData);
      setKpis(kpiData);
      setInsights(insightsData.insights);
      setActions(actionsData.actions);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  const handleRefresh = async () => {
    await loadData();
  };

  const handleTokenSave = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!tokenInput) {
      return;
    }
    setToken(tokenInput);
    setTokenInput("");
  };

  const handleTokenClear = () => {
    clearToken();
  };

  const handleToggleAction = async (action: ActionItem) => {
    const nextStatus = action.status === "open" ? "done" : "open";
    try {
      await apiFetch(`/actions/${action.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus })
      });
      setActions((prev) =>
        prev.map((item) => (item.id === action.id ? { ...item, status: nextStatus } : item))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update action.");
    }
  };

  const [organizationId, setOrganizationId] = useState("");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [kpis, setKpis] = useState<KpiLatestResponse | null>(null);
  const [insights, setInsights] = useState<InsightApi[]>([]);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [copilotMessage, setCopilotMessage] = useState("");
  const [copilotResponse, setCopilotResponse] = useState<string | null>(null);
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(() => Boolean(getTokens()));
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    if (!organizationId) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const [healthResponse, kpiResponse, insightResponse, actionsResponse] = await Promise.all([
        apiFetch<HealthResponse>(`/health/latest?organization_id=${organizationId}`),
        apiFetch<KpiLatestResponse>(`/kpis/latest?organization_id=${organizationId}`),
        apiFetch<InsightsResponse>(`/insights/latest?organization_id=${organizationId}`),
        apiFetch<ActionsResponse>(`/actions/open?organization_id=${organizationId}`)
      const [healthResponse, kpiResponse, insightResponse] = await Promise.all([
        apiFetch<HealthResponse>(`/health/latest?organization_id=${organizationId}`),
        apiFetch<KpiLatestResponse>(`/kpis/latest?organization_id=${organizationId}`),
        apiFetch<InsightsResponse>(`/insights/latest?organization_id=${organizationId}`)
      ]);
      setHealth(healthResponse);
      setKpis(kpiResponse);
      setInsights(insightResponse.insights);
      setActions(actionsResponse.actions);
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

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAuthError(null);

    try {
      const response = await apiFetch<{
        access_token: string;
        refresh_token: string;
      }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });
      setTokens({
        accessToken: response.access_token,
        refreshToken: response.refresh_token
      });
      setIsAuthenticated(true);
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : "Unable to login.");
    }
  };

  const handleLogout = () => {
    clearTokens();
    setIsAuthenticated(false);
  };

  const handleCopilot = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!organizationId || !copilotMessage) {
      return;
    }
    setCopilotLoading(true);
    setCopilotResponse(null);
    try {
      const response = await apiFetch<CopilotResponse>("/ai/chat", {
        method: "POST",
        body: JSON.stringify({ organization_id: organizationId, message: copilotMessage })
      });
      setCopilotResponse(response.content);
      setCopilotMessage("");
    } catch (err) {
      setCopilotResponse(err instanceof Error ? err.message : "Copilot request failed.");
      const response = await apiFetch<{ content: string }>(
        "/ai/chat",
        {
          method: "POST",
          body: JSON.stringify({
            organization_id: organizationId,
            message: copilotMessage
          })
        },
        true
      );
      setCopilotResponse(response.content);
      setCopilotMessage("");
    } catch (err) {
      setCopilotResponse(err instanceof Error ? err.message : "Unable to reach Copilot.");
    } finally {
      setCopilotLoading(false);
    }
  };

  const kpiCards = useMemo(() => {
    if (!kpis) {
      return [];
    }
    return Object.entries(kpis.metrics).map(([metric, value]) => ({
      label: metric.replace(/_/g, " "),
      metric: metric.replace(/_/g, " "),
      value
    }));
  }, [kpis]);

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-6 py-16">
      <header className="flex flex-col gap-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
              AION OS Dashboard
            </p>
            <h1 className="text-3xl font-semibold text-white">AI-first operating view</h1>
          </div>
          <button
            type="button"
            onClick={handleRefresh}
            className="inline-flex items-center justify-center rounded-full border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition hover:border-slate-500"
          >
            Refresh
          </button>
      <section className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-400">
              AION Dashboard
            </p>
            <h1 className="text-3xl font-semibold text-white">Organization Pulse</h1>
          </div>
          <div className="flex flex-wrap gap-3">
            {isAuthenticated ? (
              <button
                type="button"
                onClick={handleLogout}
                className="inline-flex items-center justify-center rounded-full border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition hover:border-slate-500"
              >
                Log out
              </button>
            ) : null}
            <button
              type="button"
              onClick={handleRecompute}
              disabled={!organizationId || isLoading}
              className="inline-flex items-center justify-center rounded-full border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition hover:border-slate-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Recompute
            </button>
          </div>
        </div>
        <div className="grid gap-4 lg:grid-cols-[2fr_3fr]">
          <label className="flex flex-col gap-2 text-sm text-slate-300">
            Organization ID
            <input
              value={organizationId}
              onChange={(event) => setOrganizationId(event.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white placeholder:text-slate-500"
              placeholder="UUID"
            />
          </label>
          <form onSubmit={handleTokenSave} className="flex flex-col gap-2">
            <p className="text-sm text-slate-400">JWT token</p>
            <div className="flex flex-wrap items-center gap-2">
              <input
                value={tokenInput}
                onChange={(event) => setTokenInput(event.target.value)}
                className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500"
                placeholder="Paste aion_token"
              />
              <button
                type="submit"
                className="rounded-full border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-semibold text-white"
              >
                Save
              </button>
              <button
                type="button"
                onClick={handleTokenClear}
                className="rounded-full border border-slate-700 bg-transparent px-4 py-2 text-sm font-semibold text-slate-200"
              >
                Clear
              </button>
            </div>
            <p className="text-xs text-slate-500">
              {isAuthenticated ? "Token loaded." : "Token not set."}
            </p>
          </form>
        </div>
              placeholder="UUID"
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white placeholder:text-slate-500"
            />
          </label>
          <form onSubmit={handleLogin} className="flex flex-col gap-2">
            <p className="text-sm text-slate-400">Auth session</p>
            <div className="grid gap-2 sm:grid-cols-2">
              <input
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="Email"
                className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500"
                type="email"
              />
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Password"
                className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500"
                type="password"
              />
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="submit"
                disabled={!email || !password}
                className="inline-flex items-center justify-center rounded-full border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition hover:border-slate-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Log in
              </button>
              {authError && <span className="text-xs text-rose-300">{authError}</span>}
            </div>
          </form>
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
      </header>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Health score</p>
          {loading ? (
            <div className="mt-6 h-10 w-32 animate-pulse rounded bg-slate-800" />
          ) : (
            <div className="mt-4 flex items-end gap-3">
              <span className="text-5xl font-semibold text-white">
                {health ? health.score : "--"}
              </span>
              <span className="text-sm text-slate-400">/ 100</span>
            </div>
          )}
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
            {loading && kpiCards.length === 0 ? (
              Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="h-20 animate-pulse rounded-xl bg-slate-800" />
              ))
            ) : kpiCards.length > 0 ? (
              kpiCards.map((item) => (
                <div
                  key={item.label}
                  className="rounded-xl border border-slate-800 bg-slate-950/70 p-3"
                >
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
                    {item.label}
            {kpiCards.length > 0 ? (
              kpiCards.map((item) => (
                <div
                  key={item.metric}
                  className="rounded-xl border border-slate-800 bg-slate-950/70 p-3"
                >
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
                    {item.metric}
                  </p>
                  <p className="mt-2 text-lg font-semibold text-white">{item.value.toFixed(2)}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-400">No KPI data loaded.</p>
            )}
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <div className="flex items-center justify-between">
            <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Insights feed</p>
            {loading && <span className="text-xs text-slate-400">Loading...</span>}
            <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Insights</p>
            {isLoading && <span className="text-xs text-slate-400">Refreshing...</span>}
          </div>
          <div className="mt-4 space-y-4">
            {insights.length > 0 ? (
              insights.map((insight) => {
                const severity = insight.severity === "info" ? "low" : insight.severity;
                return (
                  <div
                    key={insight.id}
                    className="rounded-xl border border-slate-800 bg-slate-950/70 p-4"
                  >
                    <div className="flex flex-wrap items-center gap-3">
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${severityStyles[severity]}`}
                      >
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
              <p className="text-sm text-slate-400">No insights available.</p>
              <p className="text-sm text-slate-300">
                {organizationId
                  ? "No insights available."
                  : "Enter an organization ID to view insights."}
              </p>
            )}
          </div>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Open actions</p>
          <div className="mt-4 space-y-3">
            {actions.length > 0 ? (
              actions.map((action) => (
                <div
                  key={action.id}
                  className="rounded-xl border border-slate-800 bg-slate-950/70 p-3"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-white">{action.title}</p>
                    <button
                      type="button"
                      onClick={() => handleToggleAction(action)}
                      className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-200"
                    >
                      Mark {action.status === "open" ? "done" : "open"}
                    </button>
                  </div>
                <div key={action.id} className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
                  <p className="text-sm font-semibold text-white">{action.title}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {action.due_at ? `Due ${new Date(action.due_at).toLocaleDateString()}` : "No due date"}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-400">No open actions.</p>
            )}
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
          <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Copilot chat</p>
          <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Copilot</p>
          {copilotLoading && <span className="text-xs text-slate-400">Thinking...</span>}
        </div>
        <form onSubmit={handleCopilot} className="mt-4 flex flex-col gap-3">
          <textarea
            value={copilotMessage}
            onChange={(event) => setCopilotMessage(event.target.value)}
            placeholder="Ask Copilot about KPIs, risks, or actions..."
            placeholder="Ask Copilot about your KPIs, risks, or actions..."
            className="min-h-[120px] rounded-lg border border-slate-700 bg-slate-900 p-3 text-sm text-white placeholder:text-slate-500"
          />
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={!copilotMessage}
              className="inline-flex items-center justify-center rounded-full border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition hover:border-slate-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Send
            </button>
              disabled={!organizationId || !copilotMessage || !isAuthenticated}
              className="inline-flex items-center justify-center rounded-full border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition hover:border-slate-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Send to Copilot
            </button>
            {!isAuthenticated && (
              <span className="text-xs text-slate-400">Login required to chat.</span>
            )}
          </div>
        </form>
        {copilotResponse && (
          <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-sm text-slate-200">
            {copilotResponse}
          </div>
        )}
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
