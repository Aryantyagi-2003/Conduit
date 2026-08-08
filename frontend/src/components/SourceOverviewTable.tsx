import type { JobRunOut, SourceOut } from "../lib/types";
import { SOURCE_DISPLAY } from "../lib/sourceConfig";
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

export function SourceOverviewTable({
  sources,
  latestRunBySource,
}: {
  sources: SourceOut[];
  latestRunBySource: Map<string, JobRunOut>;
}) {
  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-surface">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
            <th className="px-4 py-3 font-medium">Source</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Last run</th>
            <th className="px-4 py-3 font-medium">Rows processed</th>
            <th className="px-4 py-3 font-medium">Interval</th>
            <th className="px-4 py-3 font-medium">Next run</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((s) => {
            const run = latestRunBySource.get(s.source_id);
            const display = SOURCE_DISPLAY[s.source_id];
            return (
              <tr key={s.source_id} className="border-b border-border last:border-0 hover:bg-surface-2">
                <td className="px-4 py-3 font-medium text-text">{display?.label ?? s.source_id}</td>
                <td className="px-4 py-3">
                  <FreshnessBadge status={s.freshness_status} />
                </td>
                <td className="px-4 py-3">
                  {run ? (
                    <span className="flex items-center gap-2">
                      <RunStatusBadge status={run.status} />
                      <span className="font-data text-xs text-text-faint">
                        {relativeTime(run.finished_at ?? run.started_at)}
                      </span>
                    </span>
                  ) : (
                    <span className="font-data text-xs text-text-faint">no runs yet</span>
                  )}
                </td>
                <td className="font-numeric px-4 py-3 text-base text-text">
                  {run?.rows_loaded ?? <span className="text-text-faint">—</span>}
                </td>
                <td className="px-4 py-3 font-data text-xs text-text-muted">{s.interval_seconds}s</td>
                <td className="px-4 py-3">
                  <NextRunCountdown lastSuccessAt={s.last_success_at} intervalSeconds={s.interval_seconds} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
