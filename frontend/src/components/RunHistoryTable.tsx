import { useState } from "react";
import type { ReactNode } from "react";
import type { JobRunOut } from "../lib/types";
import { RunStatusBadge } from "./StatusBadge";
import { SOURCE_DISPLAY } from "../lib/sourceConfig";

const STATUSES = ["success", "failed", "running", "partial"];

/** Narrow-column form for the ledger's fixed-width Time cell: "HH:MM".
 * The full ISO timestamp (and any error) is still available via the
 * row's title attribute. */
function formatTimeShort(iso: string): string {
  return iso.replace("Z", "").split("T")[1].slice(0, 5);
}

function RailButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full rounded-md px-2 py-1 text-left text-xs transition-colors ${
        active ? "bg-accent-muted font-medium text-accent-strong" : "text-text-muted hover:bg-surface-2"
      }`}
    >
      {children}
    </button>
  );
}

/** Run history as a side "ledger" -- a vertical filter rail (source,
 * then status) instead of dropdowns, paired with a tall scrolling log.
 * Same filtering logic/state as before, just a denser terminal-log feel
 * to match the bento layout instead of a header-bar-with-two-<select>s.
 */
export function RunHistoryTable({ runs }: { runs: JobRunOut[] }) {
  const [sourceFilter, setSourceFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const sourceIds = Array.from(new Set(runs.map((r) => r.source_id))).sort();

  const filtered = runs.filter(
    (r) =>
      (sourceFilter === "all" || r.source_id === sourceFilter) &&
      (statusFilter === "all" || r.status === statusFilter)
  );

  return (
    <div className="flex h-full flex-col rounded-lg border border-border bg-surface">
      <div className="border-b border-border px-4 py-3">
        <h3 className="font-serif text-xl text-text">Run history</h3>
        <p className="text-xs text-text-faint">Every scheduled execution, filterable</p>
      </div>

      <div className="flex min-h-0 flex-1">
        <div className="w-24 shrink-0 space-y-4 border-r border-border p-2">
          <div>
            <div className="mb-1 px-2 text-[10px] font-medium uppercase tracking-wide text-text-faint">Source</div>
            <div className="space-y-0.5">
              <RailButton active={sourceFilter === "all"} onClick={() => setSourceFilter("all")}>
                All
              </RailButton>
              {sourceIds.map((id) => (
                <RailButton key={id} active={sourceFilter === id} onClick={() => setSourceFilter(id)}>
                  {SOURCE_DISPLAY[id]?.label ?? id}
                </RailButton>
              ))}
            </div>
          </div>
          <div>
            <div className="mb-1 px-2 text-[10px] font-medium uppercase tracking-wide text-text-faint">Status</div>
            <div className="space-y-0.5">
              <RailButton active={statusFilter === "all"} onClick={() => setStatusFilter("all")}>
                All
              </RailButton>
              {STATUSES.map((s) => (
                <RailButton key={s} active={statusFilter === s} onClick={() => setStatusFilter(s)}>
                  {s}
                </RailButton>
              ))}
            </div>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-surface">
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
                <th className="px-2 py-2 font-medium">Source</th>
                <th className="px-2 py-2 font-medium">Status</th>
                <th className="px-2 py-2 font-medium">Time</th>
                <th className="px-2 py-2 font-medium">Rows</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((run) => (
                <tr
                  key={run.id}
                  title={`#${run.id} · ${run.scheduled_for}${run.error ? " — " + run.error : ""}`}
                  className="border-b border-border last:border-0 hover:bg-surface-2"
                >
                  <td className="px-2 py-2 text-text">{SOURCE_DISPLAY[run.source_id]?.label ?? run.source_id}</td>
                  <td className="px-2 py-2">
                    <span className="flex items-center gap-1.5">
                      <RunStatusBadge status={run.status} />
                      {run.error && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-critical" aria-label="error" />}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-2 py-2 font-data text-xs text-text-muted">
                    {formatTimeShort(run.scheduled_for)}
                  </td>
                  <td className="font-numeric px-2 py-2 text-text">{run.rows_loaded ?? "—"}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-2 py-6 text-center text-sm text-text-faint">
                    No runs match this filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
