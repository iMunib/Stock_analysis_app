/** Compare basket persisted to localStorage (Phase 9: key `compareIds`, max 8). */

const KEY = "compareIds";
const MAX = 8;

export function getCompareSelection(): string[] {
  try {
    const raw = localStorage.getItem(KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === "string").slice(0, MAX) : [];
  } catch {
    return [];
  }
}

export function toggleCompareSelection(id: string): string[] {
  const cur = getCompareSelection();
  const next = (cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id]).slice(0, MAX);
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    /* storage unavailable â€” in-memory only */
  }
  return next;
}

export function clearCompareSelection(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}


