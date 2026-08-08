import { useState } from "react";
import type { JobRunOut } from "../lib/types";
import { RunStatusBadge } from "./StatusBadge";
import { SOURCE_DISPLAY } from "../lib/sourceConfig";

const STATUSES = ["success", "failed", "running", "partial"];

function formatTimestamp(iso: string): string {
  return iso.replace("T", " ").replace("Z", "").slice(0, 19);
}

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
    <div className="rounded-lg border border-border bg-surface">
      <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
        <h3 className="text-sm font-medium text-text">Run history</h3>
        <div className="flex gap-2">
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="rounded-md border border-border-strong bg-surface-2 px-2 py-1 text-xs text-text focus:border-accent focus:outline-none"
          >
            <option value="all">All sources</option>
            {sourceIds.map((id) => (
              <option key={id} value={id}>
                {SOURCE_DISPLAY[id]?.label ?? id}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-md border border-border-strong bg-surface-2 px-2 py-1 text-xs text-text focus:border-accent focus:outline-none"
          >
            <option value="all">All statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="max-h-96 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-surface">
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
              <th className="px-4 py-2 font-medium">ID</th>
              <th className="px-4 py-2 font-medium">Source</th>
              <th className="px-4 py-2 font-medium">Status</th>
              <th className="px-4 py-2 font-medium">Scheduled for</th>
              <th className="px-4 py-2 font-medium">Started</th>
              <th className="px-4 py-2 font-medium">Rows</th>
              <th className="px-4 py-2 font-medium">Error</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((run) => (
              <tr key={run.id} className="border-b border-border last:border-0 hover:bg-surface-2">
                <td className="px-4 py-2 font-data text-xs text-text-faint">{run.id}</td>
                <td className="px-4 py-2 text-text">{SOURCE_DISPLAY[run.source_id]?.label ?? run.source_id}</td>
                <td className="px-4 py-2">
                  <RunStatusBadge status={run.status} />
                </td>
                <td className="px-4 py-2 font-data text-xs text-text-muted">
                  {formatTimestamp(run.scheduled_for)}
                </td>
                <td className="px-4 py-2 font-data text-xs text-text-muted">{formatTimestamp(run.started_at)}</td>
                <td className="font-numeric px-4 py-2 text-text">{run.rows_loaded ?? "—"}</td>
                <td className="max-w-xs truncate px-4 py-2 font-data text-xs text-critical" title={run.error ?? ""}>
                  {run.error ?? ""}
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-sm text-text-faint">
                  No runs match this filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
