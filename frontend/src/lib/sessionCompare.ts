/** Session compare basket (sessionStorage). Survives navigation, not the browser. */

const KEY = "compare-selection";
const MAX = 8;

export function getCompareSelection(): string[] {
  try {
    const raw = sessionStorage.getItem(KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === "string") : [];
  } catch {
    return [];
  }
}

export function toggleCompareSelection(id: string): string[] {
  const cur = getCompareSelection();
  const next = cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id];
  const capped = next.slice(0, MAX);
  try {
    sessionStorage.setItem(KEY, JSON.stringify(capped));
  } catch {
    /* storage unavailable — in-memory only */
  }
  return capped;
}

export function clearCompareSelection(): void {
  try {
    sessionStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}
