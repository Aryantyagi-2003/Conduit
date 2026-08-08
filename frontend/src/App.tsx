import { useMemo } from "react";
import { api } from "./lib/api";
import { usePolling } from "./hooks/usePolling";
import { SOURCE_DISPLAY } from "./lib/sourceConfig";
import { SourceOverviewTable } from "./components/SourceOverviewTable";
import { SourceChart } from "./components/SourceChart";
import { RunHistoryTable } from "./components/RunHistoryTable";
import type { JobRunOut } from "./lib/types";

const SOURCE_IDS = Object.keys(SOURCE_DISPLAY);

function App() {
  const { data: sources, error: sourcesError } = usePolling(() => api.sources(), 10_000);
  const { data: runs, error: runsError } = usePolling(() => api.runs({ limit: 100 }), 10_000);
  const { data: weatherRows } = usePolling(() => api.data("weather", 80), 15_000);
  const { data: cryptoRows } = usePolling(() => api.data("crypto", 80), 15_000);
  const { data: githubRows } = usePolling(() => api.data("github", 80), 30_000);

  const latestRunBySource = useMemo(() => {
    const map = new Map<string, JobRunOut>();
    for (const run of runs ?? []) {
      if (!map.has(run.source_id)) map.set(run.source_id, run);
    }
    return map;
  }, [runs]);

  const totalRowsRecent = useMemo(() => {
    return (runs ?? []).reduce((sum, r) => sum + (r.rows_loaded ?? 0), 0);
  }, [runs]);

  const failedRunsRecent = (runs ?? []).filter((r) => r.status === "failed").length;

  return (
    <div className="mx-auto min-h-screen max-w-6xl px-6 py-8">
      <header className="mb-8 flex flex-wrap items-end justify-between gap-4 border-b border-border pb-6">
        <div>
          <h1 className="font-serif text-3xl font-semibold tracking-tight text-text">Conduit</h1>
          <p className="mt-1 text-sm text-text-muted">
            Self-hosted data pipeline — extract, transform, load, observe.
          </p>
        </div>
        <div className="flex gap-6">
          <Stat label="Sources" value={String(SOURCE_IDS.length)} />
          <Stat label="Rows (recent runs)" value={totalRowsRecent.toLocaleString()} />
          <Stat
            label="Failed runs (recent)"
            value={String(failedRunsRecent)}
            tone={failedRunsRecent > 0 ? "critical" : undefined}
          />
        </div>
      </header>

      {(sourcesError || runsError) && (
        <div className="mb-6 rounded-lg border border-critical bg-critical-bg px-4 py-3 text-sm text-critical">
          Could not reach the API ({sourcesError ?? runsError}). Is the backend running on :8000?
        </div>
      )}

      <section className="mb-10">
        <SectionHeading title="Pipeline health" subtitle="Last run, freshness, and schedule per source" />
        {sources ? (
          <SourceOverviewTable sources={sources} latestRunBySource={latestRunBySource} />
        ) : (
          <LoadingBlock />
        )}
      </section>

      <section className="mb-10">
        <SectionHeading title="Recent values" subtitle="Latest observations per source" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <SourceChart sourceId="weather" rows={weatherRows ?? []} />
          <SourceChart sourceId="crypto" rows={cryptoRows ?? []} />
          <SourceChart sourceId="github" rows={githubRows ?? []} />
        </div>
      </section>

      <section>
        <SectionHeading title="Run history" subtitle="Every scheduled execution, filterable" />
        {runs ? <RunHistoryTable runs={runs} /> : <LoadingBlock />}
      </section>

      <footer className="mt-10 border-t border-border pt-4 text-xs text-text-faint">
        Data from Open-Meteo, CoinGecko, and the GitHub REST API. Polling every 10–30s.
      </footer>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: "critical" }) {
  return (
    <div className="text-right">
      <div className={`font-numeric text-2xl font-semibold ${tone === "critical" ? "text-critical" : "text-text"}`}>
        {value}
      </div>
      <div className="text-xs uppercase tracking-wide text-text-faint">{label}</div>
    </div>
  );
}

function SectionHeading({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="mb-3">
      <h2 className="text-base font-semibold text-text">{title}</h2>
      <p className="text-xs text-text-faint">{subtitle}</p>
    </div>
  );
}

function LoadingBlock() {
  return (
    <div className="flex h-32 items-center justify-center rounded-lg border border-border bg-surface text-sm text-text-faint">
      Loading…
    </div>
  );
}

export default App;
