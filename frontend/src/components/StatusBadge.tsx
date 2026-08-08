import type { FreshnessStatus } from "../lib/types";

const FRESHNESS_META: Record<FreshnessStatus, { label: string; dot: string; text: string; bg: string }> = {
  fresh: { label: "Fresh", dot: "bg-fresh", text: "text-fresh", bg: "bg-fresh-bg" },
  stale: { label: "Stale", dot: "bg-stale", text: "text-stale", bg: "bg-stale-bg" },
  critical: { label: "Critical", dot: "bg-critical", text: "text-critical", bg: "bg-critical-bg" },
};

export function FreshnessBadge({ status }: { status: FreshnessStatus }) {
  const meta = FRESHNESS_META[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium ${meta.bg} ${meta.text}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} aria-hidden />
      {meta.label}
    </span>
  );
}

const RUN_STATUS_META: Record<string, { label: string; text: string; bg: string }> = {
  success: { label: "Success", text: "text-fresh", bg: "bg-fresh-bg" },
  failed: { label: "Failed", text: "text-critical", bg: "bg-critical-bg" },
  running: { label: "Running", text: "text-accent-strong", bg: "bg-accent-muted" },
  partial: { label: "Partial", text: "text-stale", bg: "bg-stale-bg" },
};

export function RunStatusBadge({ status }: { status: string }) {
  const meta = RUN_STATUS_META[status] ?? { label: status, text: "text-text-muted", bg: "bg-surface-2" };
  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${meta.bg} ${meta.text}`}>
      {meta.label}
    </span>
  );
}
