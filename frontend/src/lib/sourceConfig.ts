export interface SourceDisplayConfig {
  label: string;
  entityKey: string;
  metricKey: string;
  metricLabel: string;
  unit: string;
  formatMetric: (v: number) => string;
  formatAxisTick: (v: number) => string;
}

const compact = new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 });

export const SOURCE_DISPLAY: Record<string, SourceDisplayConfig> = {
  weather: {
    label: "Weather",
    entityKey: "location_id",
    metricKey: "temperature_c",
    metricLabel: "Temperature",
    unit: "°C",
    formatMetric: (v) => v.toFixed(1),
    formatAxisTick: (v) => v.toFixed(0),
  },
  crypto: {
    label: "Crypto",
    entityKey: "asset_symbol",
    metricKey: "price_usd",
    metricLabel: "Price",
    unit: "USD",
    formatMetric: (v) => (v >= 1000 ? v.toLocaleString(undefined, { maximumFractionDigits: 0 }) : v.toFixed(2)),
    formatAxisTick: (v) => compact.format(v),
  },
  github: {
    label: "GitHub",
    entityKey: "repo_full_name",
    metricKey: "stars",
    metricLabel: "Stars",
    unit: "",
    formatMetric: (v) => v.toLocaleString(),
    formatAxisTick: (v) => compact.format(v),
  },
};

export const SERIES_COLORS = ["var(--color-series-1)", "var(--color-series-2)", "var(--color-series-3)"];
