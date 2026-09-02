// @vitest-environment jsdom
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Home from "./Home";
import * as clientModule from "../api/client";

describe("Home Ingest State Machine and Quick Try", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    (window as unknown as { fetch: unknown }).fetch = vi.fn().mockResolvedValue({
      json: async () => ({ items: [] }),
    });
    vi.spyOn(clientModule.api, "researchMeta").mockResolvedValue({
      companies: 720,
      scored: 713,
      insufficient_data: 7,
      growth_null: 713,
      signal_histogram: {},
    } as any);
    vi.spyOn(clientModule.api, "rankings").mockResolvedValue({ items: [] } as any);
  });

  afterEach(() => {
    cleanup();
  });

  it("renders quick try chips for AMD, BABA, SHOP.TO, KITS.TO", async () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    );

    expect(await screen.findByText("AMD")).toBeTruthy();
    expect(screen.getByText("BABA")).toBeTruthy();
    expect(screen.getByText("SHOP.TO")).toBeTruthy();
    expect(screen.getByText("KITS.TO")).toBeTruthy();
  });

  it("starts ingest job and shows step progress pills when quick chip clicked", async () => {
    vi.spyOn(clientModule.api, "ingest").mockResolvedValue({
      job_id: "fake-job-123",
      status: "queued",
      step: "queued",
      message: "Job queued",
      company_id: "US:AMD:US",
    });
    vi.spyOn(clientModule.api, "job").mockResolvedValue({
      id: "fake-job-123",
      kind: "ingest",
      status: "running",
      step: "filings",
      message: "Fetching annual filings for AMD...",
      company_id: "US:AMD:US",
      error_code: null,
      error: null,
      progress_done: 0,
      progress_total: 1,
    } as any);

    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    );

    const amdChip = await screen.findByText("AMD");
    fireEvent.click(amdChip);

    expect(await screen.findByText("Filings")).toBeTruthy();
    expect(screen.getByText("Resolve")).toBeTruthy();
    expect(screen.getByText("Score")).toBeTruthy();
  });
});
