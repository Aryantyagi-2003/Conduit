import type { DataRow, JobRunOut, SourceOut } from "./types";

const BASE = "";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    throw new Error(`${path} -> ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => get<{ status: string; database: string }>("/health"),
  sources: () => get<SourceOut[]>("/api/sources"),
  data: (sourceId: string, limit = 60) =>
    get<DataRow[]>(`/api/data/${sourceId}?limit=${limit}`),
  runs: (params: { sourceId?: string; status?: string; limit?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.sourceId) qs.set("source_id", params.sourceId);
    if (params.status) qs.set("status", params.status);
    qs.set("limit", String(params.limit ?? 50));
    return get<JobRunOut[]>(`/api/runs?${qs.toString()}`);
  },
  exportCsvUrl: (sourceId: string) => `${BASE}/api/data/${sourceId}/export.csv`,
};
