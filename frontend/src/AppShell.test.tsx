// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import AppShell from "./components/AppShell";

describe("app shell nav renders without crashing (mock fetch)", () => {
  beforeEach(() => {
    // Mock the jobs probe (nav shows Jobs only if reachable) and any search fetch.
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        ({ ok: true, status: 200, text: async () => JSON.stringify({ items: [] }), json: async () => ({ items: [] }) }) as unknown as Response,
      ),
    );
  });

  it("renders the three core nav routes", async () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <AppShell>
          <div>page-content</div>
        </AppShell>
      </MemoryRouter>,
    );
    expect(screen.getByText("Desk")).toBeTruthy();
    expect(screen.getByText("Sectors")).toBeTruthy();
    expect(screen.getByText("Compare")).toBeTruthy();
    expect(screen.getByText("page-content")).toBeTruthy();
    expect(screen.getByText(/Not investment advice/)).toBeTruthy();
  });
});
