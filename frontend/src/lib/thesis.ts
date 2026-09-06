/** LocalStorage thesis notepad helper. Key: thesis:{company_id}, max 1000 chars. */

export const THESIS_MAX_CHARS = 1000;

export interface ThesisData {
  text: string;
  preMortem?: string;
  savedAt: string | null;
}

export function thesisKey(companyId: string): string {
  return `thesis:${companyId}`;
}

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

export function getThesis(companyId: string): ThesisData {
  if (!companyId) return { text: "", preMortem: "", savedAt: null };
  const store = getStorage();
  if (!store) return { text: "", preMortem: "", savedAt: null };
  try {
    const raw = store.getItem(thesisKey(companyId));
    if (!raw) return { text: "", preMortem: "", savedAt: null };
    const parsed = JSON.parse(raw);
    if (typeof parsed === "object" && parsed !== null) {
      return {
        text: typeof parsed.text === "string" ? parsed.text.slice(0, THESIS_MAX_CHARS) : "",
        preMortem: typeof parsed.preMortem === "string" ? parsed.preMortem.slice(0, THESIS_MAX_CHARS) : "",
        savedAt: typeof parsed.savedAt === "string" ? parsed.savedAt : null,
      };
    }
    // Fallback if raw string was saved
    return { text: String(raw).slice(0, THESIS_MAX_CHARS), preMortem: "", savedAt: null };
  } catch {
    return { text: "", preMortem: "", savedAt: null };
  }
}

export function saveThesis(companyId: string, text: string, preMortem?: string): ThesisData {
  const truncated = text.slice(0, THESIS_MAX_CHARS);
  const truncatedPm = typeof preMortem === "string" ? preMortem.slice(0, THESIS_MAX_CHARS) : "";
  const data: ThesisData = {
    text: truncated,
    preMortem: truncatedPm,
    savedAt: new Date().toISOString(),
  };
  const store = getStorage();
  if (store) {
    try {
      store.setItem(thesisKey(companyId), JSON.stringify(data));
    } catch {
      /* storage unavailable */
    }
  }
  return data;
}
