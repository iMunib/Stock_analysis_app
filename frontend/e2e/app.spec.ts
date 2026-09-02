import { expect, test } from "@playwright/test";

test.describe("Phase 9 — All-currency default + shell", () => {
  test("desk loads", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /the desk/i })).toBeVisible();
  });

  test("sectors hub defaults to All", async ({ page }) => {
    await page.goto("/sectors");
    await expect(page.getByRole("heading", { name: "Sectors", exact: true })).toBeVisible();
    const allBtn = page.getByRole("button", { name: "ALL", exact: true });
    await expect(allBtn).toHaveAttribute("aria-pressed", "true");
    await expect(page.getByText(/\d+ USD \/ \d+ CAD/i).first()).toBeVisible();
  });

  test("Banks All → combined score table + two money panels", async ({ page }) => {
    await page.goto("/sectors/Banks?currency=ALL");
    // ALL view fires 3 API calls (rankings + USD/CAD snapshots); under parallel
    // worker load the composed panel can take >15s on first render.
    await expect(page.getByText("USD money medians")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText("CAD money medians")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/Ranked companies/)).toBeVisible();
    await expect(page.locator("td", { hasText: "USD" }).first()).toBeVisible();
    await expect(page.locator("td", { hasText: "CAD" }).first()).toBeVisible();
  });

  test("Banks CAD → money-only single view, no USD rows", async ({ page }) => {
    await page.goto("/sectors/Banks?currency=CAD");
    await expect(page.getByText(/Ranked companies/)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("USD money medians")).toHaveCount(0);
    const badges = await page.locator("td", { hasText: "USD" }).count();
    expect(badges).toBe(0);
  });

  test("RY dossier shows verdict + pillar bars", async ({ page }) => {
    await page.goto(`/c/${encodeURIComponent("CA:RY:TSX")}`);
    await expect(page.getByRole("heading", { name: /Royal Bank/i })).toBeVisible();
    await expect(page.getByText(/of 8/).first()).toBeVisible();
    await expect(page.getByRole("heading", { name: /How it scores/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /Why this score/i })).toBeVisible();
  });

  test("compare AAPL+RY shows mixed-currency warning", async ({ page }) => {
    await page.goto(`/compare?ids=${encodeURIComponent("US:AAPL:US")},${encodeURIComponent("CA:RY:TSX")}`);
    await expect(page.getByRole("alert")).toContainText(/Mixed currencies/i, { timeout: 15_000 });
  });

  test("junk id → friendly 404, no white screen", async ({ page }) => {
    await page.goto(`/c/${encodeURIComponent("US:JUNKZZ:US")}`);
    await expect(page.getByText(/Company not found/i)).toBeVisible();
    await expect(page.getByText(/Not investment advice/i)).toBeVisible(); // footer still there
  });

  test("reduced motion disables animations", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/sectors");
    const anim = await page.evaluate(() => {
      const el = document.querySelector(".animate-fade-in") as HTMLElement | null;
      return el ? getComputedStyle(el).animationName : "none";
    });
    expect(["none", ""]).toContain(anim);
  });
});
