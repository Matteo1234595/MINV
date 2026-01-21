const highlights = [
  {
    title: "System Status",
    description: "Monitor cluster health, latency, and uptime at a glance."
  },
  {
    title: "Automations",
    description: "Deploy intelligent workflows that keep your systems aligned."
  },
  {
    title: "Telemetry",
    description: "Unified event streams for observability across services."
  }
];

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-10 px-6 py-16">
      <section className="space-y-4">
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-400">
          AION OS
        </p>
        <h1 className="text-4xl font-semibold text-white md:text-5xl">
          Orchestrate adaptive infrastructure.
        </h1>
        <p className="max-w-2xl text-lg text-slate-300">
          AION OS brings realtime telemetry, automation, and secure operations into a
          single control plane.
        </p>
      </section>
      <section className="grid gap-6 md:grid-cols-3">
        {highlights.map((highlight) => (
          <div
            key={highlight.title}
            className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6"
          >
            <h2 className="text-lg font-semibold text-white">
              {highlight.title}
            </h2>
            <p className="mt-2 text-sm text-slate-300">
              {highlight.description}
            </p>
          </div>
        ))}
      </section>
      <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <p className="text-sm text-slate-300">
          Connect the API at <span className="font-mono">/health</span> to keep the
          dashboard informed.
        </p>
        <div className="mt-4">
          <a
            href="/dashboard"
            className="inline-flex items-center rounded-full border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition hover:border-slate-500"
          >
            Go to Dashboard
          </a>
        </div>
      </section>
    </main>
  );
}
