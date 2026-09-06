/** Compare basket persisted to localStorage (key `compareIds`, max 8).
 *  Atomic event-driven store - every mutation dispatches `compare-updated`
 *  so all views (AppShell badge, Dossier star, Compare table) stay in sync
 *  without requiring a navigation change. Storage events also propagate
 *  across tabs.
 */

import { useCallback, useEffect, useState } from "react";

export const COMPARE_KEY = "compareIds";
export const COMPARE_MAX = 8;
export const COMPARE_EVENT = "compare-updated";

const KEY = COMPARE_KEY;
const MAX = COMPARE_MAX;
const EVENT = COMPARE_EVENT;

function dispatchCompareUpdated(ids: string[]): void {
  try {
    window.dispatchEvent(new CustomEvent<string[]>(EVENT, { detail: ids }));
  } catch {
    /* non-browser or dispatch unavailable */
  }
  // Also fire a plain Event for listeners that ignore CustomEvent detail
  try {
    window.dispatchEvent(new Event(EVENT));
  } catch {
    /* ignore */
  }
}

export function getCompareSelection(): string[] {
  try {
    const raw = localStorage.getItem(KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === "string").slice(0, MAX) : [];
  } catch {
    return [];
  }
}

function setCompareSelection(next: string[]): string[] {
  const sliced = next.filter((x): x is string => typeof x === "string").slice(0, MAX);
  try {
    localStorage.setItem(KEY, JSON.stringify(sliced));
  } catch {
    /* storage unavailable - in-memory only */
  }
  dispatchCompareUpdated(sliced);
  return sliced;
}

export function toggleCompareSelection(id: string): string[] {
  const cur = getCompareSelection();
  const next = (cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id]).slice(0, MAX);
  return setCompareSelection(next);
}

export function addCompareSelection(id: string): string[] {
  const cur = getCompareSelection();
  if (cur.includes(id)) return cur;
  if (cur.length >= MAX) return cur;
  return setCompareSelection([...cur, id]);
}

export function removeCompareSelection(id: string): string[] {
  const cur = getCompareSelection();
  if (!cur.includes(id)) return cur;
  return setCompareSelection(cur.filter((x) => x !== id));
}

export function clearCompareSelection(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
  dispatchCompareUpdated([]);
}

/** Explicit atomic clear used by Compare tray - empties state, clears
 *  localStorage, dispatches `compare-updated`, and clears active comparison
 *  query parameters in the URL when called from a router context (see
 *  `useCompare().clearCompare()` which also patches history).
 */
export function clearCompare(): void {
  clearCompareSelection();
  try {
    const url = new URL(window.location.href);
    if (url.searchParams.has("ids") || url.searchParams.has("compareIds")) {
      url.searchParams.delete("ids");
      url.searchParams.delete("compareIds");
      window.history.replaceState({}, "", url.pathname + (url.search ? `?${url.searchParams.toString()}` : "") + url.hash);
      // Notify router listeners that URL changed without full reload
      window.dispatchEvent(new PopStateEvent("popstate"));
    }
  } catch {
    /* ignore URL patch failures */
  }
}

/** Atomic event-driven hook - single source of truth for the compare basket.
 *  Subscribes to `compare-updated` and `storage` events so background
 *  mutations (e.g. Dossier "Add to Compare") immediately propagate to every
 *  mounted consumer (AppShell badge, Compare table, Dossier star).
 */
export function useCompare() {
  const [ids, setIds] = useState<string[]>(() => getCompareSelection());

  useEffect(() => {
    const handler = () => {
      setIds(getCompareSelection());
    };
    const customHandler = (e: Event) => {
      const ce = e as CustomEvent<string[]>;
      if (Array.isArray(ce.detail)) {
        setIds(ce.detail.slice(0, MAX));
      } else {
        handler();
      }
    };
    window.addEventListener(EVENT, customHandler as EventListener);
    window.addEventListener("storage", handler);
    // Also sync on visibility return (bfcache)
    document.addEventListener("visibilitychange", handler);
    return () => {
      window.removeEventListener(EVENT, customHandler as EventListener);
      window.removeEventListener("storage", handler);
      document.removeEventListener("visibilitychange", handler);
    };
  }, []);

  const add = useCallback((id: string): string[] => {
    const next = addCompareSelection(id);
    setIds(next);
    return next;
  }, []);

  const remove = useCallback((id: string): string[] => {
    const next = removeCompareSelection(id);
    setIds(next);
    return next;
  }, []);

  const toggle = useCallback((id: string): string[] => {
    const next = toggleCompareSelection(id);
    setIds(next);
    return next;
  }, []);

  const set = useCallback((next: string[]): string[] => {
    const result = setCompareSelection(next);
    setIds(result);
    return result;
  }, []);

  const clear = useCallback((): void => {
    clearCompareSelection();
    setIds([]);
  }, []);

  const clearCompareFn = useCallback((): void => {
    clear();
    try {
      const url = new URL(window.location.href);
      if (url.searchParams.has("ids") || url.searchParams.has("compareIds")) {
        url.searchParams.delete("ids");
        url.searchParams.delete("compareIds");
        window.history.replaceState({}, "", url.pathname + (url.search ? `?${url.searchParams.toString()}` : "") + url.hash);
        window.dispatchEvent(new PopStateEvent("popstate"));
      }
    } catch {
      /* ignore */
    }
  }, [clear]);

  const has = useCallback((id: string) => ids.includes(id), [ids]);

  return {
    ids,
    count: ids.length,
    has,
    add,
    remove,
    toggle,
    set,
    clear,
    clearCompare: clearCompareFn,
    MAX,
    KEY,
    EVENT,
  };
}

