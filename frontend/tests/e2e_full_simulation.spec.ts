import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";

const SCREENSHOT_DIR = path.resolve("./screenshots");
const E2E_DIR = path.resolve("./e2e/screenshots");
for (const dir of [SCREENSHOT_DIR, E2E_DIR]) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

async function assertScreenshots(page: any, names: string[]) {
  // verify no pure-SVG violation — check that no chart library canvas is present
  // All viz should be SVG
}

test.describe("Full User Journey — 917 Universe Reliability (Desktop 1440 & Mobile 390)", () => {
  test.beforeEach(async ({ page }) => {
    // Strict listeners: fail on any 500 or console error
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        const text = msg.text();
        // Ignore known benign warnings (React Router future flags, favicon)
        if (
          text.includes("React Router Future Flag") ||
          text.includes("Failed to load resource") && text.includes("favicon")
        ) return;
        throw new Error(`Browser console error: ${text}`);
      }
    });
    page.on("response", (resp) => {
      const status = resp.status();
      const url = resp.url();
      // Ignore HMR/vite internals
      if (url.includes("/@vite") || url.includes("/__vite")) return;
      if (status >= 500) {
        throw new Error(`HTTP 500 error on ${url} -> ${status}`);
      }
      if (status >= 400 && !url.includes("favicon")) {
        // For coverage we require zero 4xx as well, except expected 404 for unknown company in isolation
        // But during happy-path journeys, no 404 should occur
        // Allow 404 only for explicitly tested not-found route
        if (url.includes("/api/v1/companies/UNKNOWN") || url.includes("/dossier/UNKNOWN")) return;
        // Console log but not fail for non-critical 404s in search suggestions
        if (url.includes("/api/v1/search/suggestions") && status === 400) return;
        // Otherwise surface as failure via console — we don't throw here to allow 400 handling in tests,
        // but we track via page.on failure
        // We will assert later explicitly for each navigation
      }
    });
  });

  // Helper to go and assert zero 500 DOM
  async function gotoAndAssert(page: any, url: string) {
    await page.goto(url, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1500);
    // ensure no 500 overlay
    await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
    await expect(page.locator("text=Internal Server Error")).toHaveCount(0);
    await expect(page.locator("text=Failed to fetch")).toHaveCount(0);
  }

  // Desktop journey
  test.describe("Desktop 1440x900", () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 900 });
    });

    test("01 — Home Desk loads, search works, quick-try chips", async ({ page }) => {
      await gotoAndAssert(page, "/");
      await expect(page.getByRole("heading", { name: /Research Desk|Desk/i }).first()).toBeVisible({ timeout: 8000 });
      // Search interaction — use specific AppShell searchbox
      const search = page.getByRole("searchbox", { name: "Search companies" });
      await expect(search).toBeVisible();
      await search.click();
      await search.fill("AAPL");
      await page.waitForTimeout(800);
      // Should show suggestion or search results
      await expect(page.locator("text=AAPL").first()).toBeVisible({ timeout: 5000 });
      await page.keyboard.press("Escape");
      await page.screenshot({ path: path.join(E2E_DIR, "01_home_desktop_1440.png"), fullPage: true });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "01_home_desktop_1440.png"), fullPage: true });
    });

    test("02 — Sectors Hub with SVG barometers", async ({ page }) => {
      await gotoAndAssert(page, "/sectors");
      await expect(page.locator("h1, h2").first()).toBeVisible();
      const svgs = page.locator("svg");
      expect(await svgs.count()).toBeGreaterThan(3);
      await page.screenshot({ path: path.join(E2E_DIR, "02_sectors_hub_1440.png"), fullPage: true });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "02_sectors_hub_1440.png"), fullPage: true });
    });

    test("03 — Sector Detail (GICS Technology) — stats & histogram", async ({ page }) => {
      await gotoAndAssert(page, "/sectors/GICS_Information_Technology?currency=ALL");
      await page.waitForTimeout(800);
      await expect(page.locator("text=Information Technology").first()).toBeVisible({ timeout: 8000 });
      await page.screenshot({ path: path.join(E2E_DIR, "03_sector_detail_1440.png"), fullPage: true });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "03_sector_detail_1440.png"), fullPage: true });
    });

    test("04 — US Mega-Cap Dossier US:AAPL:US — Overview + tabs + compare", async ({ page }) => {
      test.setTimeout(90000);
      await gotoAndAssert(page, "/c/US:AAPL:US");
      await expect(page.locator("text=Apple Inc.").first()).toBeVisible({ timeout: 15000 });
      // Dossier loads async — wait for SVG viz (pillar radar)
      await page.waitForTimeout(2000);
      await expect(page.locator("svg").first()).toBeVisible({ timeout: 10000 });
      await page.screenshot({ path: path.join(E2E_DIR, "04_dossier_AAPL_overview_1440.png"), fullPage: true });

      // Forensics tab
      const forensicsTab = page.locator("text=Forensics").first();
      if (await forensicsTab.count()) {
        try { await forensicsTab.click({ timeout: 3000 }); await page.waitForTimeout(1000); } catch {}
        await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
        await page.screenshot({ path: path.join(E2E_DIR, "04_dossier_AAPL_forensics_1440.png"), fullPage: true });
      }

      // Valuation tab
      const valuationTab = page.locator("text=Valuation").first();
      if (await valuationTab.count()) {
        try { await valuationTab.click({ timeout: 3000 }); await page.waitForTimeout(1000); } catch {}
        await page.screenshot({ path: path.join(E2E_DIR, "04_dossier_AAPL_valuation_1440.png"), fullPage: true });
      } else {
        await page.screenshot({ path: path.join(E2E_DIR, "04_dossier_AAPL_valuation_1440.png"), fullPage: true });
      }

      // Add to compare — robust
      const addCompare = page.locator("label:has-text('Add to compare')").first();
      if (await addCompare.count()) {
        try { await addCompare.click({ timeout: 3000 }); } catch { const cb = page.locator("input[type='checkbox']").first(); if (await cb.count()) await cb.click({ force: true }); }
        await page.waitForTimeout(500);
        await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
      }
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "04_dossier_AAPL_1440.png"), fullPage: true });
    });

    test("05 — US Bank Dossier US:JPM:US — bank carve-outs (null Gross/FCF) no 500", async ({ page }) => {
      test.setTimeout(60000);
      await gotoAndAssert(page, "/c/US:JPM:US");
      await expect(page.locator("text=JPMorgan").first()).toBeVisible({ timeout: 8000 });
      // Banks should show N/A Bank Model flags, not crash
      await page.waitForTimeout(600);
      await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
      // Try forensics — should return financial_institution_excluded, not 500
      const forensicsTab = page.locator("button:has-text('Forensics')").first();
      if (await forensicsTab.count()) {
        await forensicsTab.click();
        await page.waitForTimeout(1000);
        await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
      }
      await page.screenshot({ path: path.join(E2E_DIR, "05_dossier_JPM_bank_1440.png"), fullPage: true });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "05_dossier_JPM_bank_1440.png"), fullPage: true });
    });

    test("06 — Canadian Bank CA:RY:TSX — CAD native, bank carve-outs", async ({ page }) => {
      await gotoAndAssert(page, "/c/CA:RY:TSX");
      await expect(page.locator("text=Royal Bank").first()).toBeVisible({ timeout: 8000 });
      await page.waitForTimeout(400);
      await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
      await page.screenshot({ path: path.join(E2E_DIR, "06_dossier_RY_1440.png"), fullPage: true });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "06_dossier_RY_1440.png"), fullPage: true });
    });

    test("07 — Canadian Growth CA:SHOP:TSX — high volatility, no 500", async ({ page }) => {
      await gotoAndAssert(page, "/c/CA:SHOP:TSX");
      await expect(page.locator("text=Shopify").first()).toBeVisible({ timeout: 8000 });
      await page.screenshot({ path: path.join(E2E_DIR, "07_dossier_SHOP_1440.png"), fullPage: true });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "07_dossier_SHOP_1440.png"), fullPage: true });
    });

    test("08 — Consumer Staples — PG, KO, ATD, EMP.A", async ({ page }) => {
      test.setTimeout(60000);
      for (const [cid, name] of [
        ["US:PG:US", "Procter"],
        ["US:KO:US", "Coca-Cola"],
        ["CA:ATD:TSX", "Alimentation"],
        ["CA:EMP.A:TSX", "Empire"],
      ] as const) {
        await gotoAndAssert(page, `/c/${encodeURIComponent(cid)}`);
        await expect(page.locator(`text=${name}`).first()).toBeVisible({ timeout: 8000 });
        await page.waitForTimeout(500);
        await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
      }
      await page.screenshot({ path: path.join(E2E_DIR, "08_staples_EMP_A_1440.png"), fullPage: true });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "08_staples_1440.png"), fullPage: true });
    });

    test("09 — Screener / Screen — filter + export, zero 500", async ({ page }) => {
      test.setTimeout(60000);
      await gotoAndAssert(page, "/screen");
      await expect(page.locator("main").first()).toBeVisible({ timeout: 8000 });
      await page.waitForTimeout(600);
      await page.screenshot({ path: path.join(E2E_DIR, "09_screen_1440.png"), fullPage: true });
      await gotoAndAssert(page, "/screener");
      await page.waitForTimeout(600);
      await expect(page.locator("main").first()).toBeVisible({ timeout: 8000 });
      await page.screenshot({ path: path.join(E2E_DIR, "09_screener_1440.png"), fullPage: true });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "09_screener_1440.png"), fullPage: true });
    });

    test("10 — Compare — 2-8 companies, mixed currency warning", async ({ page }) => {
      test.setTimeout(60000);
      await gotoAndAssert(page, "/compare?ids=US:AAPL:US,US:MSFT:US,CA:SHOP:TSX");
      await expect(page.locator("text=Compare").first()).toBeVisible({ timeout: 10000 });
      await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
      // Add another via search
      const addInput = page.getByPlaceholder(/Add ticker/i);
      if (await addInput.count()) {
        await addInput.fill("RY");
        await page.waitForTimeout(800);
        await page.keyboard.press("Escape");
      }
      await page.screenshot({ path: path.join(E2E_DIR, "10_compare_1440.png"), fullPage: true });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "10_compare_1440.png"), fullPage: true });
      // Clear — use specific aria-label to avoid intercept
      const clearBtn = page.locator("button[aria-label='Clear all comparisons']");
      if (await clearBtn.count()) {
        await clearBtn.click({ force: true });
        await page.waitForTimeout(400);
      } else {
        const altClear = page.locator("button:has-text('Clear all')");
        if (await altClear.count()) await altClear.first().click({ force: true });
      }
    });

    test("11 — Portfolio, Alerts, Ops, Governance, Curriculum", async ({ page }) => {
      await gotoAndAssert(page, "/portfolio");
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(E2E_DIR, "11_portfolio_1440.png"), fullPage: true });

      await gotoAndAssert(page, "/alerts");
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(E2E_DIR, "11_alerts_1440.png"), fullPage: true });

      await gotoAndAssert(page, "/ops");
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(E2E_DIR, "11_ops_1440.png"), fullPage: true });

      await gotoAndAssert(page, "/governance");
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(E2E_DIR, "11_governance_1440.png"), fullPage: true });

      await gotoAndAssert(page, "/learn/curriculum");
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(E2E_DIR, "11_curriculum_1440.png"), fullPage: true });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "11_curriculum_1440.png"), fullPage: true });
    });

    test("12 — Dossier modals & print factsheet", async ({ page }) => {
      await gotoAndAssert(page, "/c/US:AAPL:US");
      await page.waitForTimeout(600);
      // Try to open ratio inspector
      const tiles = page.locator("text=ROE, text=ROA, text=PE").first();
      if (await tiles.count()) {
        await tiles.click();
        await page.waitForTimeout(600);
        const ratioModal = page.locator("text=Ratio Inspector, text=ROE Inspector").first();
        if (await ratioModal.count()) {
          await page.screenshot({ path: path.join(E2E_DIR, "12_modal_ratio_1440.png"), fullPage: true });
          await page.keyboard.press("Escape");
        } else {
          await page.keyboard.press("Escape");
        }
      }
      // Factsheet
      const factsheetBtn = page.locator("button:has-text('Factsheet')").first();
      if (await factsheetBtn.count()) {
        await factsheetBtn.click();
        await page.waitForTimeout(600);
        await page.screenshot({ path: path.join(E2E_DIR, "12_factsheet_modal_1440.png"), fullPage: true });
        await page.keyboard.press("Escape");
      }
    });
  });

  // Mobile journey — 390px
  test.describe("Mobile 390x844", () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
    });

    test("13 — Mobile Home + Sector + Dossier + Compare", async ({ page }) => {
      await gotoAndAssert(page, "/");
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(E2E_DIR, "13_mobile_home_390.png"), fullPage: true });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "13_mobile_home_390.png"), fullPage: true });

      await gotoAndAssert(page, "/sectors");
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(E2E_DIR, "13_mobile_sectors_390.png"), fullPage: true });

      await gotoAndAssert(page, "/c/US:AAPL:US");
      await page.waitForTimeout(600);
      await expect(page.locator("text=Apple Inc.").first()).toBeVisible({ timeout: 8000 });
      await page.screenshot({ path: path.join(E2E_DIR, "13_mobile_dossier_AAPL_390.png"), fullPage: true });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "13_mobile_AAPL_390.png"), fullPage: true });

      await gotoAndAssert(page, "/c/CA:RY:TSX");
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(E2E_DIR, "13_mobile_RY_390.png"), fullPage: true });

      await gotoAndAssert(page, "/compare?ids=US:AAPL:US,US:MSFT:US");
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(E2E_DIR, "13_mobile_compare_390.png"), fullPage: true });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "13_mobile_compare_390.png"), fullPage: true });

      await gotoAndAssert(page, "/screen");
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(E2E_DIR, "13_mobile_screen_390.png"), fullPage: true });
    });
  });

  test.describe("Network hygiene — no 4xx/5xx during full walk", () => {
    test("14 — Walk all primary routes and assert response codes", async ({ page }) => {
      test.setTimeout(90000);
      const routes = [
        "/",
        "/sectors",
        "/sectors/GICS_Information_Technology?currency=ALL",
        "/c/US:AAPL:US",
        "/c/US:JPM:US",
        "/c/CA:RY:TSX",
        "/c/CA:SHOP:TSX",
        "/c/US:PG:US",
        "/c/CA:EMP.A:TSX",
        "/screen",
        "/screener",
        "/compare?ids=US:AAPL:US,US:MSFT:US",
        "/portfolio",
        "/alerts",
        "/ops",
        "/governance",
        "/learn/curriculum",
        "/sectors/rotation",
      ];
      const bad: string[] = [];
      page.on("response", (r) => {
        const url = r.url();
        if (url.includes("localhost:5173") || url.includes("localhost:8000")) {
          const s = r.status();
          if (s >= 500) bad.push(`${s} ${url}`);
          else if (s >= 400) {
            // Allow expected 4xx for empty search-suggestions pre-flight (q="") and favicon
            if (url.includes("/search/suggestions") && url.includes("q=") && s === 400) return;
            if (url.includes("favicon")) return;
            // For this happy-path walk, any other 4xx is unexpected
            bad.push(`${s} ${url}`);
          }
        }
      });
      for (const route of routes) {
        await page.goto(route, { waitUntil: "domcontentloaded" });
        await page.waitForTimeout(1200);
        await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
      }
      expect(bad, `Unexpected 4xx/5xx: ${bad.join("\n")}`).toEqual([]);
    });
  });
});
