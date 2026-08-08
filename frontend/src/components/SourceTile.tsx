import type { DataRow, JobRunOut, SourceOut } from "../lib/types";
import { SOURCE_DISPLAY } from "../lib/sourceConfig";
import { SourceChart } from "./SourceChart";
import { FreshnessBadge, RunStatusBadge } from "./StatusBadge";
import { NextRunCountdown } from "./NextRunCountdown";

function relativeTime(iso: string | null): string {
  if (!iso) return "never";
  const diffMs = Date.now() - new Date(iso).getTime();
  const s = Math.floor(diffMs / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  return `${h}h ago`;
}

/** One source's health + chart merged into a single card -- replaces the
 * old split of "a row in the health table" + "a separate chart tile".
 * `size="hero"` gets a taller chart and the full stat row spelled out;
 * `size="compact"` gets a smaller chart and a terser single-line stat.
 */
export function SourceTile({
  sourceId,
  source,
  rows,
  latestRun,
  size = "compact",
}: {
  sourceId: string;
  source: SourceOut | undefined;
  rows: DataRow[];
  latestRun: JobRunOut | undefined;
  size?: "hero" | "compact";
}) {
  const display = SOURCE_DISPLAY[sourceId];
  const isHero = size === "hero";

  return (
    <div className="flex h-full flex-col rounded-lg border border-border bg-surface p-4">
      <div className="mb-1 flex items-start justify-between gap-2">
        <div>
          <h3 className={isHero ? "font-serif text-xl text-text" : "text-sm font-medium text-text"}>
            {display?.label ?? sourceId}
          </h3>
          {isHero && (
            <span className="font-data text-xs text-text-faint">
              {display?.metricLabel} ({display?.unit || "count"})
            </span>
          )}
        </div>
        {source && <FreshnessBadge status={source.freshness_status} />}
      </div>

      <div className={isHero ? "mt-2" : "mt-1"}>
        <SourceChart sourceId={sourceId} rows={rows} height={isHero ? 220 : 96} hideHeader bare />
      </div>

      <div className="mt-3 flex items-center justify-between gap-2 border-t border-border pt-3 text-xs">
        {latestRun ? (
          <span className="flex items-center gap-1.5">
            <RunStatusBadge status={latestRun.status} />
            <span className="font-data text-text-faint">{relativeTime(latestRun.finished_at ?? latestRun.started_at)}</span>
          </span>
        ) : (
          <span className="font-data text-text-faint">no runs yet</span>
        )}
        <span className="font-numeric text-text">{latestRun?.rows_loaded ?? "—"}</span>
        {source && (
          <NextRunCountdown lastSuccessAt={source.last_success_at} intervalSeconds={source.interval_seconds} />
        )}
      </div>
    </div>
  );
}
