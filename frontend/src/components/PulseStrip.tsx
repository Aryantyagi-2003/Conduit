import type { SourceOut } from "../lib/types";
import { SOURCE_DISPLAY } from "../lib/sourceConfig";

const DOT_COLOR: Record<string, string> = {
  fresh: "bg-fresh",
  stale: "bg-stale",
  critical: "bg-critical",
};

/** Compact masthead readout replacing the old separate stat-number row:
 * one dot per source (colored + glowing when fresh, per the existing
 * freshness-glow keyframe) plus a fresh-count fraction. Same data as
 * the source tiles below, just a denser summary at a glance.
 */
export function PulseStrip({ sources }: { sources: SourceOut[] }) {
  const freshCount = sources.filter((s) => s.freshness_status === "fresh").length;

  return (
    <div className="flex items-center gap-3 rounded-full border border-border bg-surface/70 px-3 py-1.5 backdrop-blur-sm">
      <div className="flex items-center gap-1.5">
        {sources.map((s) => (
          <span
            key={s.source_id}
            title={`${SOURCE_DISPLAY[s.source_id]?.label ?? s.source_id}: ${s.freshness_status}`}
            className={`h-2 w-2 rounded-full ${DOT_COLOR[s.freshness_status] ?? "bg-text-faint"} ${
              s.freshness_status === "fresh" ? "freshness-glow" : ""
            }`}
          />
        ))}
      </div>
      <span className="font-data text-xs text-text-muted">
        {freshCount}/{sources.length} fresh
      </span>
    </div>
  );
}
