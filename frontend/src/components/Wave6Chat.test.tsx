// @vitest-environment jsdom
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import StockChatDrawer from "./StockChatDrawer";
import * as clientModule from "../api/client";

describe("Wave 6 Grounded Voice - minimax + citations + 100-word", () => {
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

  it("shows minimax default model and citation chips with 50/50 bull/bear (US-0701/US-0704/US-0705)", async () => {
    vi.spyOn(clientModule.api, "chat").mockResolvedValue({
      role: "assistant",
      content: "AI Narration (not the score)\n\nBull: Quality 7/10 durable. Bear: Value 4/10 expensive. Source: deterministic fundamentals + filed data only.",
      model_used: "minimax/minimax-m3:free",
      citations: [
        { key: "revenue", value: "391035000000", source: "financial_snapshots" },
        { key: "composite", value: "7.2", source: "scores" },
      ],
      disclaimer: "Personal research software, not investment advice. AI narration is an interpretation of local facts, not a financial endorsement.",
    } as any);

    render(<StockChatDrawer companyId="US:AAPL:US" companyName="Apple Inc." isOpen={true} onClose={() => {}} />);

    // Header shows AI Research Chat
    expect(await screen.findByText(/AI Research Chat/, {}, { timeout: 3000 })).toBeTruthy();
    expect(screen.getAllByText(/AI Narration \(not the score\)/)[0]).toBeTruthy();

    // Send a message to trigger citation rendering
    const input = screen.getByLabelText("Chat message input") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "Give me a 100-word verdict" } });
    fireEvent.click(screen.getByLabelText("Send message"));

    await waitFor(() => {
      expect(screen.getByText(/Bull:/)).toBeTruthy();
      expect(screen.getByText(/Bear:/)).toBeTruthy();
    }, { timeout: 3000 });

    // Citation chips should appear after response - check for at least one chip
    await waitFor(() => {
      const chips = document.querySelectorAll("[aria-label^='Citation']");
      expect(chips.length).toBeGreaterThan(0);
    }, { timeout: 3000 });
  });

  it("toggles 100-word, bullets, memo formats (US-0702/US-0716)", async () => {
    vi.spyOn(clientModule.api, "chat").mockResolvedValue({
      role: "assistant",
      content: "AI Narration (not the score)\n\nTest content",
      model_used: "minimax/minimax-m3:free",
      citations: [],
      disclaimer: "Personal",
    } as any);

    render(<StockChatDrawer companyId="US:AAPL:US" isOpen={true} onClose={() => {}} />);

    expect(await screen.findByText("100-word", {}, { timeout: 3000 })).toBeTruthy();
    expect(screen.getByText("Bullets")).toBeTruthy();
    expect(screen.getByText("Board Memo")).toBeTruthy();

    // Click 100-word tab should set viewMode
    fireEvent.click(screen.getByText("100-word"));
    expect(screen.getByRole("tab", { name: "100-word" }).getAttribute("aria-selected")).toBe("true");
  });

  it("shows deterministic fallback disclaimer when offline ( US-0718 )", async () => {
    // Mock chat to return deterministic fallback
    vi.spyOn(clientModule.api, "chat").mockResolvedValue({
      role: "assistant",
      content: "**AI Narration (not the score) - 100-Word Verdict**\nApple Inc. (USD) scores 7.2/10 (mixed). Bull: Quality 7/10 durable. Bear: Value 4/10 expensive.",
      model_used: "deterministic_fallback",
      citations: [{ key: "revenue", value: "100", source: "financial_snapshots" }],
      disclaimer: "Personal research software, not investment advice. AI narration is an interpretation of local facts, not a financial endorsement.",
    } as any);

    render(<StockChatDrawer companyId="US:AAPL:US" isOpen={true} onClose={() => {}} />);

    const input = screen.getByLabelText("Chat message input");
    fireEvent.change(input, { target: { value: "Hello" } });
    fireEvent.click(screen.getByLabelText("Send message"));

    await waitFor(() => {
      expect(screen.getByText(/100-Word Verdict/)).toBeTruthy();
    }, { timeout: 3000 });
    expect(screen.getByText(/deterministic_fallback/)).toBeTruthy();
  });
});