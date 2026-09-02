import { beforeEach, describe, expect, it } from "vitest";
import { evaluateAlert, getAlertForCompany, getAlerts, removeAlert, saveAlert } from "./alerts";

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

describe("local alerts helper", () => {
  beforeEach(() => {
    storageMock.clear();
  });

  it("saves and retrieves alerts", () => {
    saveAlert({ id: "US:MSFT:US", pe_above: 25, composite_below: 4.0 });
    const alerts = getAlerts();
    expect(alerts).toHaveLength(1);
    expect(alerts[0].id).toBe("US:MSFT:US");
    expect(alerts[0].pe_above).toBe(25);

    const msftAlert = getAlertForCompany("US:MSFT:US");
    expect(msftAlert).not.toBeNull();
    expect(msftAlert?.composite_below).toBe(4.0);
  });

  it("evaluates PE alert triggered", () => {
    const alert = { id: "US:MSFT:US", pe_above: 25 };
    const banner = evaluateAlert(alert, "MSFT", 27.2, 5.0);
    expect(banner).toBe("MSFT PE now 27.2 vs your alert 25");
  });

  it("evaluates composite below alert triggered", () => {
    const alert = { id: "US:AAPL:US", composite_below: 6.0 };
    const banner = evaluateAlert(alert, "AAPL", 22.0, 5.2);
    expect(banner).toBe("AAPL composite now 5.2 vs your alert 6");
  });

  it("returns null when no alert conditions are met", () => {
    const alert = { id: "US:MSFT:US", pe_above: 35, composite_below: 4.0 };
    const banner = evaluateAlert(alert, "MSFT", 27.0, 5.5);
    expect(banner).toBeNull();
  });

  it("removes an alert", () => {
    saveAlert({ id: "US:MSFT:US", pe_above: 25 });
    expect(getAlerts()).toHaveLength(1);
    removeAlert("US:MSFT:US");
    expect(getAlerts()).toHaveLength(0);
  });
});
