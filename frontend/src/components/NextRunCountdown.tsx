import { useNow } from "../hooks/usePolling";

function formatDuration(ms: number): string {
  const abs = Math.abs(ms);
  const totalSeconds = Math.floor(abs / 1000);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function NextRunCountdown({
  lastSuccessAt,
  intervalSeconds,
}: {
  lastSuccessAt: string | null;
  intervalSeconds: number;
}) {
  const now = useNow(1000);

  if (!lastSuccessAt) {
    return <span className="font-data text-xs text-text-faint">unscheduled</span>;
  }

  const nextRunAt = new Date(lastSuccessAt).getTime() + intervalSeconds * 1000;
  const remainingMs = nextRunAt - now;
  const isDue = remainingMs <= 0;

  return (
    <span className={`font-data text-xs tabular-nums ${isDue ? "text-accent-strong" : "text-text-muted"}`}>
      {isDue ? "due now" : `in ${formatDuration(remainingMs)}`}
    </span>
  );
}
