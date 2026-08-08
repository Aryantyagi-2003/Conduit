import { useMemo } from "react";
import { api } from "./lib/api";
import { usePolling } from "./hooks/usePolling";
import { SOURCE_DISPLAY } from "./lib/sourceConfig";
import { SourceTile } from "./components/SourceTile";
import { PulseStrip } from "./components/PulseStrip";
import { Atmosphere } from "./components/Atmosphere";
import { RunHistoryTable } from "./components/RunHistoryTable";
import type { JobRunOut, SourceOut } from "./lib/types";

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

  const sourceById = useMemo(() => {
    const map = new Map<string, SourceOut>();
    for (const s of sources ?? []) map.set(s.source_id, s);
    return map;
  }, [sources]);

  return (
    <div className="mx-auto min-h-screen max-w-6xl px-6 py-8">
      <header className="relative mb-8 overflow-hidden rounded-lg border border-border bg-surface/60 px-6 py-6">
        <Atmosphere />
        <div className="relative flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="font-serif text-4xl tracking-tight text-text">Conduit</h1>
            <p className="mt-1 text-sm italic text-text-muted">
              Self-hosted data pipeline — extract, transform, load, observe.
            </p>
          </div>
          {sources && <PulseStrip sources={sources} />}
        </div>
      </header>

      {(sourcesError || runsError) && (
        <div className="mb-6 rounded-lg border border-critical bg-critical-bg px-4 py-3 text-sm text-critical">
          Could not reach the API ({sourcesError ?? runsError}). Is the backend running on :8000?
        </div>
      )}

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
        <div className="flex flex-col gap-4 lg:w-2/3">
          <SourceTile
            sourceId="weather"
            source={sourceById.get("weather")}
            rows={weatherRows ?? []}
            latestRun={latestRunBySource.get("weather")}
            size="hero"
          />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <SourceTile
              sourceId="crypto"
              source={sourceById.get("crypto")}
              rows={cryptoRows ?? []}
              latestRun={latestRunBySource.get("crypto")}
            />
            <SourceTile
              sourceId="github"
              source={sourceById.get("github")}
              rows={githubRows ?? []}
              latestRun={latestRunBySource.get("github")}
            />
          </div>
        </div>

        {/* Explicit fixed height (not h-full/stretch, which would create a
            circular dependency with the left column's natural height) so
            the ledger's internal overflow-auto has a real bound to scroll
            within, independent of how tall the source tiles are. */}
        <div className="lg:h-[624px] lg:w-1/3">
          <RunHistoryTable runs={runs ?? []} />
        </div>
      </div>

      <footer className="mt-10 border-t border-border pt-4 text-xs text-text-faint">
        Data from Open-Meteo, CoinGecko, and the GitHub REST API. Polling every 10–30s. ·{" "}
        {Object.keys(SOURCE_DISPLAY).length} sources.
      </footer>
    </div>
  );
}

export default App;
