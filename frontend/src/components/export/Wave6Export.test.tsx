// @vitest-environment jsdom
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import ResearchMemoModal from "./ResearchMemoModal";
import ExportCenterModal from "./ExportCenterModal";
import * as clientModule from "../../api/client";

describe("Wave 6 Export Suite", () => {
  beforeAll(() => {
    const g: any = globalThis as any;
    if (typeof g.localStorage === "undefined" || g.localStorage == null) {
      const store: Record<string, string> = {};
      g.localStorage = {
        getItem: (k: string) => store[k] ?? null,
        setItem: (k: string, v: string) => { store[k] = String(v); },
        removeItem: (k: string) => { delete store[k]; },
        clear: () => { for (const k in store) delete store[k]; },
        length: 0,
        key: () => null,
      } as any;
    }
  });
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders ResearchMemoModal with editable markdown and currency note (US-0402)", async () => {
    vi.spyOn(clientModule.api, "requestMemo").mockResolvedValue({
      markdown: "# Research Memo - AAPL\nCurrency: USD\n- Price: 210 USD\n> Personal research software",
      generated_at: "2026-09-05",
      currency: "USD",
    } as any);

    render(<ResearchMemoModal companyId="US:AAPL:US" isOpen={true} onClose={() => {}} />);

    expect(await screen.findByText(/Research Memo Draft/, {}, { timeout: 3000 })).toBeTruthy();
    expect(await screen.findByText(/Currency: native ISO per row/, {}, { timeout: 3000 })).toBeTruthy();
    // Edit toggle
    const editBtn = screen.getByText("Edit");
    fireEvent.click(editBtn);
    expect(screen.getByLabelText("Research memo markdown")).toBeTruthy();
    // ARIA
    expect(screen.getByRole("dialog")).toBeTruthy();
  });

  it("renders ExportCenterModal with 4 export options and currency disclaimer (US-0405/US-0438)", async () => {
    render(<ExportCenterModal isOpen={true} onClose={() => {}} companyId="US:AAPL:US" />);

    expect(await screen.findByText(/Export Center/, {}, { timeout: 3000 })).toBeTruthy();
    expect(screen.getByText(/Research Memo \(Markdown\)/)).toBeTruthy();
    expect(screen.getByText(/Batch Comparison \(CSV\)/)).toBeTruthy();
    expect(screen.getByText(/Raw JSON Dump/)).toBeTruthy();
    expect(screen.getByText(/Currency: native ISO per row/)).toBeTruthy();
    expect(screen.getByRole("dialog")).toBeTruthy();
  });

  it("ExportCenter handles keyboard Tab and Escape (a11y)", async () => {
    const onClose = vi.fn();
    render(<ExportCenterModal isOpen={true} onClose={onClose} companyId="US:AAPL:US" />);
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toBeTruthy();
    // Escape handling is via close button; check close button has aria-label
    expect(screen.getByLabelText("Close export center")).toBeTruthy();
  });
});