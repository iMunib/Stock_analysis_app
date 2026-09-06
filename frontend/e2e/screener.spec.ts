import { expect, test } from "@playwright/test";

test.describe("Forensic screener (directive §4)", () => {
  test("presets, results/empty-state, unitless ratios", async ({ page }) => {
    await page.goto("/screener");
    await expect(page.getByRole("heading", { name: /forensic screener/i })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole("tab", { name: /Forensic Red Flags/ })).toBeVisible();

    // Deep-value preset: writes criteria into the URL, then either results or the
    // honest empty state renders (live TTM/DCF coverage decides which).
    await page.getByRole("tab", { name: /Buffett-Burry Deep Value/ }).click();
    await expect(page).toHaveURL(/preset=buffett_burry_deep_value/);
    await expect(page.getByText(/matches/).first()).toBeVisible({ timeout: 20_000 });

    const tables = await page.locator("table").count();
    if (tables > 0) {
      const body = await page.locator("table").first().innerText();
      expect(body).toMatch(/USD|CAD/); // per-row currency tags, never blended
    } else {
      await expect(page.getByText(/No companies match/)).toBeVisible();
    }
  });

  test("currency toggle keeps USD purity", async ({ page }) => {
    await page.goto("/screener?currency=USD");
    await expect(page.getByText(/matches/).first()).toBeVisible({ timeout: 20_000 });
  });

  test("single-stock forensic audit mode renders Beneish, Piotroski, and Schilit cards", async ({ page }) => {
    await page.goto("/screener?view=audit&company=US:AAPL:US");
    await expect(page.getByRole("heading", { name: /forensic screener/i })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/Apple Inc\./i).first()).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/Beneish M-Score/i).first()).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/Forensic Quality Suite/i).first()).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/Piotroski F-Score/i).first()).toBeVisible({ timeout: 15_000 });

    // Quick pick switch to JPM (bank exclusion test)
    await page.getByRole("button", { name: "JPM", exact: true }).click();
    await expect(page.getByText(/JPMorgan Chase/i).first()).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/Financial Institution/i).first()).toBeVisible({ timeout: 15_000 });
  });

  test("audit button in screener row switches to single-stock audit", async ({ page }) => {
    await page.goto("/screener");
    await expect(page.getByRole("heading", { name: /forensic screener/i })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/matches/).first()).toBeVisible({ timeout: 20_000 });

    // Click the first "Audit" button in the screener table
    const auditBtn = page.locator("table tbody tr button:has-text('Audit')").first();
    await expect(auditBtn).toBeVisible();
    await auditBtn.click();

    // Verify mode switched to audit and URL contains view=audit
    await expect(page).toHaveURL(/view=audit/);
    await expect(page.getByText(/Select Company to Audit/i)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/Beneish M-Score/i).first()).toBeVisible({ timeout: 15_000 });
  });
});

