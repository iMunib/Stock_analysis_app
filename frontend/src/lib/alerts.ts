/** LocalStorage alerts helper. Key: stockAlerts.
 * Evaluated only when dossier or screen loads (no push). Keep dumb.
 */

export interface AlertItem {
  id: string;
  pe_above?: number | null;
  composite_below?: number | null;
}

const ALERTS_KEY = "stockAlerts";

function getStorage() {
  try {
    if (typeof window !== "undefined" && window.localStorage && typeof window.localStorage.getItem === "function") {
      return window.localStorage;
    }
    if (typeof localStorage !== "undefined" && typeof localStorage.getItem === "function") {
      return localStorage;
    }
  } catch {
    /* storage unavailable */
  }
  return null;
}

export function getAlerts(): AlertItem[] {
  const store = getStorage();
  if (!store) return [];
  try {
    const raw = store.getItem(ALERTS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveAlert(alert: AlertItem): AlertItem[] {
  const current = getAlerts().filter((a) => a.id !== alert.id);
  if (alert.pe_above != null || alert.composite_below != null) {
    current.push(alert);
  }
  const store = getStorage();
  if (store) {
    try {
      store.setItem(ALERTS_KEY, JSON.stringify(current));
    } catch {
      /* storage unavailable */
    }
  }
  return current;
}

export function removeAlert(id: string): AlertItem[] {
  const next = getAlerts().filter((a) => a.id !== id);
  const store = getStorage();
  if (store) {
    try {
      store.setItem(ALERTS_KEY, JSON.stringify(next));
    } catch {
      /* storage unavailable */
    }
  }
  return next;
}

export function getAlertForCompany(id: string): AlertItem | null {
  return getAlerts().find((a) => a.id === id) ?? null;
}

export function evaluateAlert(
  alert: AlertItem,
  ticker: string,
  currentPe: number | null | undefined,
  currentComposite: number | null | undefined,
): string | null {
  const label = ticker || alert.id;
  if (alert.pe_above != null && currentPe != null && currentPe > alert.pe_above) {
    return `${label} PE now ${currentPe.toFixed(1)} vs your alert ${alert.pe_above}`;
  }
  if (alert.composite_below != null && currentComposite != null && currentComposite < alert.composite_below) {
    return `${label} composite now ${currentComposite.toFixed(1)} vs your alert ${alert.composite_below}`;
  }
  return null;
}
