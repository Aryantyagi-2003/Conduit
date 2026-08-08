import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DataRow } from "../lib/types";
import { SERIES_COLORS, SOURCE_DISPLAY } from "../lib/sourceConfig";

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

interface ChartPoint {
  observed_at: string;
  [entity: string]: string | number | null;
}

function pivotByEntity(rows: DataRow[], entityKey: string, metricKey: string): { points: ChartPoint[]; entities: string[] } {
  const entities = Array.from(new Set(rows.map((r) => String(r[entityKey])))).sort();
  const byTime = new Map<string, ChartPoint>();

  for (const row of rows) {
    const t = row.observed_at;
    const entity = String(row[entityKey]);
    const value = row[metricKey];
    if (!byTime.has(t)) byTime.set(t, { observed_at: t });
    const point = byTime.get(t)!;
    point[entity] = typeof value === "number" ? value : null;
  }

  const points = Array.from(byTime.values()).sort(
    (a, b) => new Date(a.observed_at).getTime() - new Date(b.observed_at).getTime()
  );
  return { points, entities };
}

export function SourceChart({ sourceId, rows }: { sourceId: string; rows: DataRow[] }) {
  const display = SOURCE_DISPLAY[sourceId];
  if (!display) return null;

  const { points, entities } = pivotByEntity(rows, display.entityKey, display.metricKey);

  if (points.length === 0) {
    return (
      <div className="flex h-56 items-center justify-center rounded-lg border border-border bg-surface text-sm text-text-faint">
        No data yet
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="mb-3 flex items-baseline justify-between">
        <h3 className="text-sm font-medium text-text">{display.label}</h3>
        <span className="font-data text-xs text-text-faint">
          {display.metricLabel} ({display.unit || "count"})
        </span>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={points} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
          <XAxis
            dataKey="observed_at"
            tickFormatter={formatTime}
            stroke="var(--color-text-faint)"
            tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }}
            tickLine={false}
            axisLine={{ stroke: "var(--color-border-strong)" }}
            minTickGap={30}
          />
          <YAxis
            stroke="var(--color-text-faint)"
            tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }}
            tickLine={false}
            axisLine={false}
            width={52}
            tickFormatter={(v: number) => display.formatAxisTick(v)}
            domain={["auto", "auto"]}
          />
          <Tooltip
            contentStyle={{
              background: "var(--color-surface-2)",
              border: "1px solid var(--color-border-strong)",
              borderRadius: 8,
              fontSize: 12,
              fontFamily: "var(--font-mono)",
            }}
            labelStyle={{ color: "var(--color-text-muted)" }}
            labelFormatter={(v) => (typeof v === "string" ? new Date(v).toLocaleString() : String(v ?? ""))}
            formatter={(value, name) => [
              typeof value === "number" ? display.formatMetric(value) : String(value ?? ""),
              String(name ?? ""),
            ]}
          />
          {entities.map((entity, i) => (
            <Line
              key={entity}
              type="monotone"
              dataKey={entity}
              name={entity}
              stroke={SERIES_COLORS[i % SERIES_COLORS.length]}
              strokeWidth={2}
              dot={false}
              connectNulls
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {entities.length > 1 && (
        <div className="mt-2 flex flex-wrap gap-3">
          {entities.map((entity, i) => (
            <span key={entity} className="flex items-center gap-1.5 font-data text-xs text-text-muted">
              <span
                className="h-0.5 w-3 rounded-full"
                style={{ background: SERIES_COLORS[i % SERIES_COLORS.length] }}
                aria-hidden
              />
              {entity}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
