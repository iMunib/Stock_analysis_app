import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { getInitialTheme, setTheme, toggleTheme, applyTheme } from "./theme";

describe("Theme Module", () => {
  let mockStorage: Record<string, string> = {};
  const originalLocalStorage = globalThis.localStorage;
  const originalDocument = globalThis.document;

  beforeEach(() => {
    mockStorage = {};
    const storageMock = {
      getItem: (key: string) => mockStorage[key] ?? null,
      setItem: (key: string, value: string) => {
        mockStorage[key] = value;
      },
      removeItem: (key: string) => {
        delete mockStorage[key];
      },
      clear: () => {
        mockStorage = {};
      },
    };
    Object.defineProperty(globalThis, "localStorage", {
      value: storageMock,
      writable: true,
      configurable: true,
    });

    const docMock = {
      documentElement: {
        setAttribute: (k: string, v: string) => {
          docMock.documentElement.attributes[k] = v;
        },
        removeAttribute: (k: string) => {
          delete docMock.documentElement.attributes[k];
        },
        getAttribute: (k: string) => docMock.documentElement.attributes[k] ?? null,
        attributes: {} as Record<string, string>,
        classList: {
          classes: new Set<string>(),
          add: (c: string) => docMock.documentElement.classList.classes.add(c),
          remove: (c: string) => docMock.documentElement.classList.classes.delete(c),
          contains: (c: string) => docMock.documentElement.classList.classes.has(c),
        },
        style: {} as Record<string, string>,
      },
    };
    Object.defineProperty(globalThis, "document", {
      value: docMock,
      writable: true,
      configurable: true,
    });

    Object.defineProperty(globalThis, "window", {
      value: {
        dispatchEvent: () => true,
        addEventListener: () => {},
        removeEventListener: () => {},
      },
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    Object.defineProperty(globalThis, "localStorage", {
      value: originalLocalStorage,
      writable: true,
      configurable: true,
    });
    Object.defineProperty(globalThis, "document", {
      value: originalDocument,
      writable: true,
      configurable: true,
    });
  });

  it("defaults to dark theme when no preference stored", () => {
    expect(getInitialTheme()).toBe("dark");
  });

  it("reads stored preference from localStorage", () => {
    mockStorage["investment_desk_theme"] = "light";
    expect(getInitialTheme()).toBe("light");
  });

  it("applies theme attribute to documentElement", () => {
    applyTheme("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    expect(document.documentElement.classList.contains("theme-light")).toBe(true);
    expect(document.documentElement.style.colorScheme).toBe("light");

    applyTheme("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(document.documentElement.classList.contains("theme-dark")).toBe(true);
    expect(document.documentElement.style.colorScheme).toBe("dark");
  });

  it("setTheme saves to localStorage and applies data-theme", () => {
    setTheme("light");
    expect(mockStorage["investment_desk_theme"]).toBe("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });

  it("toggleTheme switches between dark and light", () => {
    setTheme("dark");
    const next = toggleTheme();
    expect(next).toBe("light");
    expect(mockStorage["investment_desk_theme"]).toBe("light");

    const back = toggleTheme();
    expect(back).toBe("dark");
    expect(mockStorage["investment_desk_theme"]).toBe("dark");
  });
});
