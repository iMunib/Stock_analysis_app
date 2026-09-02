import { beforeEach, describe, expect, it } from "vitest";
import { getThesis, saveThesis, THESIS_MAX_CHARS, thesisKey } from "./thesis";

const mockStore: Record<string, string> = {};
const storageMock = {
  getItem: (k: string) => mockStore[k] ?? null,
  setItem: (k: string, v: string) => {
    mockStore[k] = String(v);
  },
  removeItem: (k: string) => {
    delete mockStore[k];
  },
  clear: () => {
    for (const k in mockStore) delete mockStore[k];
  },
};

Object.defineProperty(globalThis, "localStorage", {
  value: storageMock,
  writable: true,
});

describe("thesis notepad localStorage helper", () => {
  beforeEach(() => {
    storageMock.clear();
  });

  it("returns empty thesis when nothing is saved", () => {
    const data = getThesis("US:AAPL:US");
    expect(data.text).toBe("");
    expect(data.savedAt).toBeNull();
  });

  it("saves and retrieves thesis with timestamp", () => {
    const saved = saveThesis("US:AAPL:US", "Strong ecosystem moat with recurring services revenue.");
    expect(saved.text).toBe("Strong ecosystem moat with recurring services revenue.");
    expect(saved.savedAt).not.toBeNull();

    const loaded = getThesis("US:AAPL:US");
    expect(loaded.text).toBe("Strong ecosystem moat with recurring services revenue.");
    expect(loaded.savedAt).toBe(saved.savedAt);
  });

  it("enforces 1000 character limit", () => {
    const longText = "a".repeat(1500);
    const saved = saveThesis("US:MSFT:US", longText);
    expect(saved.text).toHaveLength(THESIS_MAX_CHARS);

    const loaded = getThesis("US:MSFT:US");
    expect(loaded.text).toHaveLength(THESIS_MAX_CHARS);
  });

  it("uses the exact key format thesis:{company_id}", () => {
    expect(thesisKey("US:AAPL:US")).toBe("thesis:US:AAPL:US");
  });
});
