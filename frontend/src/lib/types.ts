export type FreshnessStatus = "fresh" | "stale" | "critical";

export interface SourceOut {
  source_id: string;
  interval_seconds: number;
  enabled: boolean;
  freshness_status: FreshnessStatus;
  last_success_at: string | null;
  staleness_seconds: number | null;
}

export interface JobRunOut {
  id: number;
  source_id: string;
  scheduled_for: string;
  attempt: number;
  started_at: string;
  finished_at: string | null;
  status: "running" | "success" | "failed" | "partial";
  rows_extracted: number | null;
  rows_loaded: number | null;
  error: string | null;
}

export interface DataRow {
  id: number;
  observed_at: string;
  fetched_at: string;
  [key: string]: unknown;
}
