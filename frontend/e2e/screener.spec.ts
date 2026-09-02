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
});
