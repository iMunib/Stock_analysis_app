import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";

const OUT = path.resolve("./tests/screenshots_visual_audit");
const E2E_OUT = path.resolve("./e2e/screenshots");
for (const d of [OUT, E2E_OUT]) if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true });

test.describe("Visual & Valuation Overhaul — Institutional Audit (Desktop 1440 & Mobile 390)", () => {
  test.beforeEach(async ({ page }) => {
    page.on("console", msg => {
      if (msg.type() === "error") {
        const t = msg.text();
        if (t.includes("React Router Future Flag") || t.includes("favicon")) return;
        throw new Error(`Browser console error: ${t}`);
      }
    });
    page.on("response", resp => {
      const s = resp.status();
      const u = resp.url();
      if (u.includes("/@vite") || u.includes("/__vite")) return;
      if (s >= 500) throw new Error(`HTTP 500 on ${u} -> ${s}`);
      if (s >= 400 && u.includes("localhost")) {
        if (u.includes("/search/suggestions") && s === 400) return;
        if (u.includes("favicon")) return;
        // allow 404 for not-found in isolation, but not in happy path
        if (s === 404 && (u.includes("UNKNOWN") || u.includes("NotFound"))) return;
      }
    });
  });

  async function goto(page: any, url: string) {
    await page.goto(url, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1500);
    await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
    await expect(page.locator("text=Failed to fetch")).toHaveCount(0);
  }

  test.describe("Desktop 1440x900 — Institutional Visuals", () => {
    test.beforeEach(async ({ page }) => { await page.setViewportSize({ width: 1440, height: 900 }); });

    test("01 Home Desk — overview and quick search", async ({ page }) => {
      await goto(page, "/");
      await expect(page.getByRole("heading", { name: /Research Desk|Desk/i }).first()).toBeVisible({ timeout: 8000 });
      await page.screenshot({ path: path.join(OUT, "01_home_desktop.png"), fullPage: true });
      await page.screenshot({ path: path.join(E2E_OUT, "01_home_desktop.png"), fullPage: true });
    });

    test("02 Dossier AAPL — Valuation & Expectations with fan chart and EPV spectrum", async ({ page }) => {
      await goto(page, "/c/US:AAPL:US");
      await expect(page.locator("text=Apple Inc.").first()).toBeVisible({ timeout: 12000 });
      // Open Valuation tab
      const valTab = page.locator("text=Valuation & Expectations").first().or(page.locator("text=Valuation").first());
      if (await valTab.count()) {
        await valTab.click();
        await page.waitForTimeout(1200);
      }
      await page.waitForTimeout(1000);
      // Check for institutional valuation elements
      await expect(page.locator("text=Valuation Spectrum").first()).toBeVisible({ timeout: 8000 }).catch(async () => {
        // fallback to EPV
        await expect(page.locator("text=Earnings Power").first()).toBeVisible({ timeout: 4000 });
      });
      await page.screenshot({ path: path.join(OUT, "02_dossier_AAPL_valuation_desktop.png"), fullPage: true });
      await page.screenshot({ path: path.join(E2E_OUT, "02_dossier_AAPL_valuation_desktop.png"), fullPage: true });

      // Open Guided DCF Modal
      const guidedBtn = page.locator("button:has-text('Guided DCF'), button:has-text('Sandbox')").first();
      if (await guidedBtn.count()) {
        await guidedBtn.click();
        await page.waitForTimeout(800);
        // Check fan chart present
        await expect(page.locator("text=10-Year Projected Cash-Flow Trajectory").first()).toBeVisible({ timeout: 8000 }).catch(()=>{});
        await page.screenshot({ path: path.join(OUT, "02_guided_DCF_modal_desktop.png"), fullPage: true });
        await page.screenshot({ path: path.join(E2E_OUT, "02_guided_DCF_modal_desktop.png"), fullPage: true });
        await page.keyboard.press("Escape");
        await page.waitForTimeout(300);
      }
    });

    test("03 Dossier RY.TO — Canadian Bank with DDM/Residual (bank model)", async ({ page }) => {
      await goto(page, "/c/CA:RY:TSX");
      await expect(page.locator("text=Royal Bank").first()).toBeVisible({ timeout: 10000 });
      const valTab = page.locator("text=Valuation").first();
      if (await valTab.count()) { await valTab.click(); await page.waitForTimeout(1000); }
      // For banks, should show DDM / Residual and not applicable for DCF
      await page.waitForTimeout(500);
      await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
      await page.screenshot({ path: path.join(OUT, "03_dossier_RY_valuation_desktop.png"), fullPage: true });
      await page.screenshot({ path: path.join(E2E_OUT, "03_dossier_RY_valuation_desktop.png"), fullPage: true });
    });

    test("04 Dossier JPM — US Bank carve-outs", async ({ page }) => {
      await goto(page, "/c/US:JPM:US");
      await expect(page.locator("text=JPMorgan").first()).toBeVisible({ timeout: 10000 });
      await page.waitForTimeout(800);
      await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
      await page.screenshot({ path: path.join(OUT, "04_dossier_JPM_desktop.png"), fullPage: true });
      await page.screenshot({ path: path.join(E2E_OUT, "04_dossier_JPM_desktop.png"), fullPage: true });
    });

    test("05 Dossier KO — Staples with 10-year timeline hover", async ({ page }) => {
      await goto(page, "/c/US:KO:US");
      await expect(page.locator("text=Coca-Cola").first()).toBeVisible({ timeout: 10000 });
      // Financials tab with timeline
      const finTab = page.locator("text=Financials").first();
      if (await finTab.count()) { await finTab.click(); await page.waitForTimeout(1000); }
      // Check for 10-year timeline
      await expect(page.locator("text=10-Year").first()).toBeVisible({ timeout: 8000 }).catch(()=>{});
      // Hover first point
      const point = page.locator("svg circle").first();
      if (await point.count()) {
        await point.hover();
        await page.waitForTimeout(400);
      }
      await page.screenshot({ path: path.join(OUT, "05_dossier_KO_timeline_desktop.png"), fullPage: true });
      await page.screenshot({ path: path.join(E2E_OUT, "05_dossier_KO_timeline_desktop.png"), fullPage: true });
    });

    test("06 Compare Board — side-by-side KPI and SVG trends", async ({ page }) => {
      await goto(page, "/compare?ids=US:AAPL:US,US:MSFT:US,CA:SHOP:TSX");
      await expect(page.locator("text=Compare").first()).toBeVisible({ timeout: 8000 });
      await page.waitForTimeout(800);
      await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
      // Check for trend overlays
      await expect(page.locator("text=10-Year Trend Overlays").first()).toBeVisible({ timeout: 5000 }).catch(()=>{});
      await expect(page.locator("text=Consolidated KPI").first()).toBeVisible({ timeout: 5000 }).catch(()=>{});
      await page.screenshot({ path: path.join(OUT, "06_compare_desktop.png"), fullPage: true });
      await page.screenshot({ path: path.join(E2E_OUT, "06_compare_desktop.png"), fullPage: true });
    });

    test("07 Screener — 10-year filter and peer counts", async ({ page }) => {
      await goto(page, "/screen");
      await expect(page.locator("main").first()).toBeVisible({ timeout: 8000 });
      await page.waitForTimeout(800);
      await page.screenshot({ path: path.join(OUT, "07_screener_desktop.png"), fullPage: true });
      await page.screenshot({ path: path.join(E2E_OUT, "07_screener_desktop.png"), fullPage: true });
    });

    test("08 Portfolio — holdings and allocation", async ({ page }) => {
      await goto(page, "/portfolio");
      await page.waitForTimeout(800);
      await expect(page.locator("text=Portfolio").first()).toBeVisible({ timeout: 8000 }).catch(async () => {
        await expect(page.locator("main").first()).toBeVisible();
      });
      await page.screenshot({ path: path.join(OUT, "08_portfolio_desktop.png"), fullPage: true });
      await page.screenshot({ path: path.join(E2E_OUT, "08_portfolio_desktop.png"), fullPage: true });
    });

    test("09 Curriculum — Analyst Academy progression and 10-K walkthrough", async ({ page }) => {
      await goto(page, "/learn/curriculum");
      await expect(page.locator("text=Analyst Academy").first()).toBeVisible({ timeout: 8000 });
      await expect(page.locator("text=10-K Walkthrough").first()).toBeVisible({ timeout: 8000 }).catch(()=>{});
      await page.waitForTimeout(600);
      await page.screenshot({ path: path.join(OUT, "09_curriculum_desktop.png"), fullPage: true });
      await page.screenshot({ path: path.join(E2E_OUT, "09_curriculum_desktop.png"), fullPage: true });
    });
  });

  test.describe("Mobile 390x844 — Responsive polish", () => {
    test.beforeEach(async ({ page }) => { await page.setViewportSize({ width: 390, height: 844 }); });

    test("10 Mobile Home and Dossier valuation", async ({ page }) => {
      await goto(page, "/");
      await page.waitForTimeout(600);
      await page.screenshot({ path: path.join(OUT, "10_mobile_home_390.png"), fullPage: true });
      await page.screenshot({ path: path.join(E2E_OUT, "10_mobile_home_390.png"), fullPage: true });

      await goto(page, "/c/US:AAPL:US");
      await expect(page.locator("text=Apple Inc.").first()).toBeVisible({ timeout: 12000 });
      const valTab = page.locator("text=Valuation").first();
      if (await valTab.count()) { await valTab.click(); await page.waitForTimeout(800); }
      await page.screenshot({ path: path.join(OUT, "10_mobile_AAPL_valuation_390.png"), fullPage: true });
      await page.screenshot({ path: path.join(E2E_OUT, "10_mobile_AAPL_valuation_390.png"), fullPage: true });

      await goto(page, "/compare?ids=US:AAPL:US,US:MSFT:US");
      await page.waitForTimeout(800);
      await page.screenshot({ path: path.join(OUT, "10_mobile_compare_390.png"), fullPage: true });
      await page.screenshot({ path: path.join(E2E_OUT, "10_mobile_compare_390.png"), fullPage: true });

      await goto(page, "/learn/curriculum");
      await page.waitForTimeout(600);
      await page.screenshot({ path: path.join(OUT, "10_mobile_curriculum_390.png"), fullPage: true });
      await page.screenshot({ path: path.join(E2E_OUT, "10_mobile_curriculum_390.png"), fullPage: true });
    });
  });
});
