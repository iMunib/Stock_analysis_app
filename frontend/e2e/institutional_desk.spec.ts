import { test, expect } from "@playwright/test";

test.describe("Institutional Local Equity Desk E2E", () => {
  test("Screener renders presets, indicator filters, and export CSV button", async ({ page }) => {
    await page.goto("http://localhost:5173/screener");
    await page.waitForLoadState("networkidle");

    // Check header
    await expect(page.locator("h1")).toContainText(/screener/i);

    // Check system presets tabs
    await expect(page.getByRole("tab", { name: /Buffett-Burry Deep Value/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /Forensic Red Flags/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /Discounted Compounders/i })).toBeVisible();

    // Check newly added indicator filters in sidebar
    await expect(page.getByText("Altman Z Zone")).toBeVisible();
    await expect(page.getByRole("button", { name: "Safe" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Grey" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Distress" })).toBeVisible();

    // Check Export CSV button
    await expect(page.getByRole("button", { name: /Export to CSV/i })).toBeVisible();

    // Click Buffett-Burry preset and verify URL params update
    await page.getByRole("tab", { name: /Buffett-Burry Deep Value/i }).click();
    expect(page.url()).toContain("preset=buffett_burry_deep_value");
    expect(page.url()).toContain("roic_min=0.15");
  });

  test("Dossier tabbed workspace, URL persistence, and analytical components", async ({ page }) => {
    await page.goto("http://localhost:5173/c/US:AAPL:US");
    await page.waitForLoadState("networkidle");

    // 1. Verify company identity & hero card
    await expect(page.locator("h1")).toContainText("Apple");

    // Verify Remove from Desk button
    const removeBtn = page.getByRole("button", { name: "✕ Remove from Desk" });
    await expect(removeBtn).toBeVisible();
    await removeBtn.click();
    await expect(page.getByText("Remove from desk?")).toBeVisible();
    await expect(page.getByRole("button", { name: "Yes, remove" })).toBeVisible();
    await page.getByRole("button", { name: "Cancel" }).click();
    await expect(removeBtn).toBeVisible();

    // 2. Verify Overview tab (default)
    await expect(page.getByText("Latest snapshot")).toBeVisible();
    await expect(page.getByText("How it scores")).toBeVisible();

    // 3. Navigate to Financials tab & verify URL persistence
    await page.getByRole("tab", { name: /Financials/i }).click();
    expect(page.url()).toContain("tab=financials");
    await expect(page.getByText("Annual history")).toBeVisible();
    await expect(page.getByText(/Common-Size Statements/i)).toBeVisible();
    await expect(page.getByText(/Cash-flow bridge/i)).toBeVisible();

    // 4. Navigate to Valuation tab
    await page.getByRole("tab", { name: /Valuation/i }).click();
    expect(page.url()).toContain("tab=valuation");
    await expect(page.getByText("Deterministic Reverse DCF")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("Market-Implied 10Y FCF CAGR")).toBeVisible();
    await expect(page.getByText(/Sector Percentile Matrix/i)).toBeVisible();
    await expect(page.getByText(/Graham Value Floor/i)).toBeVisible();
    await expect(page.getByText(/Index Opportunity Cost Hurdle/i)).toBeVisible();

    // 5. Navigate to Forensics tab
    await page.getByRole("tab", { name: /Forensics/i }).click();
    expect(page.url()).toContain("tab=forensics");
    await expect(page.getByText("Forensic Quality Suite")).toBeVisible();
    await expect(page.getByText("Sloan Accruals")).toBeVisible();
    await expect(page.getByText(/Penman Economic Engine/i)).toBeVisible();
    await expect(page.getByText(/Altman Solvency & Distress/i)).toBeVisible();

    // 6. Navigate to Capital Allocation tab
    await page.getByRole("tab", { name: /Capital/i }).click();
    expect(page.url()).toContain("tab=capital");
    await expect(page.getByText(/Capital Return & Share Dilution/i)).toBeVisible();
    await expect(page.getByText(/Total Shareholder Yield/i)).toBeVisible();

    // 7. Navigate to Technicals & Chart tab
    await page.getByRole("tab", { name: /Technicals/i }).click();
    expect(page.url()).toContain("tab=technicals");
    await expect(page.getByText(/Interactive Technical Chart/i)).toBeVisible();

    // 8. Test Slide-Over Fact-Grounded AI Research Assistant
    const aiBtn = page.getByRole("button", { name: /Ask Analyst AI/i });
    await expect(aiBtn).toBeVisible();
    await aiBtn.click();
    await expect(page.getByText("Analyst AI")).toBeVisible();
    await expect(page.getByText(/What are the biggest accounting red flags\?/i)).toBeVisible();
    await expect(page.getByText(/AI draft grounded in verified local facts/i)).toBeVisible();
    await page.getByRole("button", { name: "Close chat" }).click();
    await expect(page.getByText(/What are the biggest accounting red flags\?/i)).not.toBeVisible();
  });
});
