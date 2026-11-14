/**
 * Display formatting only. These helpers never compute scientific values;
 * they render numbers that the backend already returned. `null` (an
 * undefined or unavailable value) is always shown as an explicit dash.
 */

export const NOT_AVAILABLE = "—";

export function formatNumber(
  value: number | null | undefined,
  fractionDigits = 1,
): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return NOT_AVAILABLE;
  }
  return value.toLocaleString("en-US", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

export function formatSigned(
  value: number | null | undefined,
  fractionDigits = 2,
): string {
  const text = formatNumber(value, fractionDigits);
  if (text === NOT_AVAILABLE || value === null || value === undefined) {
    return text;
  }
  return value > 0 ? `+${text}` : text;
}

export function formatPValue(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return NOT_AVAILABLE;
  }
  if (value < 0.001) return "< 0.001";
  return value.toFixed(3);
}

export function formatInterval(
  interval: readonly [number | null, number | null],
  fractionDigits = 2,
): string {
  const [low, high] = interval;
  if (low === null || high === null) return NOT_AVAILABLE;
  return `${formatSigned(low, fractionDigits)} to ${formatSigned(high, fractionDigits)}`;
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return NOT_AVAILABLE;
  }
  return `${Math.round(value * 100)}%`;
}

export function formatBBox(bbox: readonly number[]): string {
  const [west, south, east, north] = bbox.map((v) => v.toFixed(2));
  return `W ${west}°, S ${south}°, E ${east}°, N ${north}°`;
}

export function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date
    .toISOString()
    .replace("T", " ")
    .replace(/\.\d+Z$/, " UTC");
}

export function humanize(identifier: string): string {
  const text = identifier.replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}
