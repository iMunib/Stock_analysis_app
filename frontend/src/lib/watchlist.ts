/** Watchlist (Phase 10 E): localStorage key `watchIds`, Company_ID[], max 50. */

const KEY = "watchIds";
const MAX = 50;

export function getWatchlist(): string[] {
  try {
    const raw = localStorage.getItem(KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === "string").slice(0, MAX) : [];
  } catch {
    return [];
  }
}

export function toggleWatch(id: string): string[] {
  const cur = getWatchlist();
  const next = (cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id]).slice(0, MAX);
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    /* storage unavailable */
  }
  return next;
}

export function isWatched(id: string): boolean {
  return getWatchlist().includes(id);
}

export function recordOpened(id: string): void {
  try {
    localStorage.setItem(`opened:${id}`, new Date().toISOString());
  } catch {
    /* storage unavailable */
  }
}

export function getOpenedAt(id: string): string | null {
  try {
    return localStorage.getItem(`opened:${id}`);
  } catch {
    return null;
  }
}


