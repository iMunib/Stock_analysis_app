import { test, expect } from "@playwright/test";

test.describe("Institutional Local Equity Desk E2E", () => {
  test("Screener renders presets and export CSV button", async ({ page }) => {
    await page.goto("http://localhost:5173/screen");
    await page.waitForLoadState("networkidle");

    // Check header
    await expect(page.locator("h1")).toContainText("Screener");

    // Check system presets buttons
    await expect(page.getByRole("button", { name: "💎 Buffett-Burry Deep Value" })).toBeVisible();
    await expect(page.getByRole("button", { name: "🚩 Forensic Red Flags" })).toBeVisible();
    await expect(page.getByRole("button", { name: "🚀 Discounted Compounders" })).toBeVisible();

    // Check Export CSV button
    await expect(page.getByRole("button", { name: "⬇ Export CSV" })).toBeVisible();

    // Click Buffett-Burry preset and verify URL params update
    await page.getByRole("button", { name: "💎 Buffett-Burry Deep Value" }).click();
    expect(page.url()).toContain("roe_min=15");
    expect(page.url()).toContain("fcf_margin_min=7");
  });

  test("Dossier renders Forensic Suite, Reverse DCF, and Remove button", async ({ page }) => {
    await page.goto("http://localhost:5173/c/US:AAPL:US");
    await page.waitForLoadState("networkidle");

    // Verify company identity
    await expect(page.locator("h1")).toContainText("Apple");

    // Verify Remove from Desk button
    const removeBtn = page.getByRole("button", { name: "✕ Remove from Desk" });
    await expect(removeBtn).toBeVisible();

    // Clicking Remove from Desk shows confirmation
    await removeBtn.click();
    await expect(page.getByText("Remove from desk?")).toBeVisible();
    await expect(page.getByRole("button", { name: "Yes, remove" })).toBeVisible();
    await page.getByRole("button", { name: "Cancel" }).click();
    await expect(removeBtn).toBeVisible();

    // Verify Forensic Quality Suite
    await expect(page.getByText("Forensic Quality Suite")).toBeVisible();
    await expect(page.getByText("Sloan Accruals")).toBeVisible();
    await expect(page.getByText("Cash Conversion (CCER)")).toBeVisible();

    // Verify Deterministic Reverse DCF
    await expect(page.getByText("Deterministic Reverse DCF")).toBeVisible();
    await expect(page.getByText("Market-Implied 10Y FCF CAGR")).toBeVisible();
    await expect(page.getByText("Sensitivity Matrix: Implied Growth Rate")).toBeVisible();
  });
});
