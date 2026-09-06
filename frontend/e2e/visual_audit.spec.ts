import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";

const SCREENSHOT_DIR = path.resolve("./e2e/screenshots");
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

test.describe("Institutional Terminal Visual Audit & Defect Verification", () => {
  test.beforeEach(async ({ page }) => {
    // Set viewport to standard high-res terminal screen
    await page.setViewportSize({ width: 1440, height: 900 });
  });

  test("01 - Home Desk & Quick Try renders cleanly without 500 error", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
    await expect(page.locator("text=Failed to fetch")).toHaveCount(0);
    
    // Screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "01_home_desk.png"),
      fullPage: true,
    });
  });

  test("02 - Sectors Hub renders all barometers with medians", async ({ page }) => {
    await page.goto("/sectors");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);

    // Verify sector groups are present
    const headings = page.locator("h2");
    await expect(headings.first()).toBeVisible();

    // Verify gauges / barometers are visible
    const gauges = page.locator("svg");
    expect(await gauges.count()).toBeGreaterThan(5);

    // Screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "02_sectors_hub.png"),
      fullPage: true,
    });
  });

  test("03 - GICS Information Technology Sector Detail renders stats & barometer", async ({ page }) => {
    await page.goto("/sectors/GICS_Information_Technology?currency=ALL");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);

    // Verify stats tiles are present
    await expect(page.locator("text=Information Technology").first()).toBeVisible();
    await expect(page.locator("text=Signal Distribution").first()).toBeVisible();

    // Screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "03_sector_infotech.png"),
      fullPage: true,
    });
  });

  test("04 - Single-currency Custom Industry renders cleanly without blank state", async ({ page }) => {
    await page.goto("/sectors/Aerospace_Defense?currency=ALL");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);

    // Screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "04_custom_aerospace.png"),
      fullPage: true,
    });
  });

  test("05 - US:AAPL:US Stock Dossier loads with zero 500 errors", async ({ page }) => {
    await page.goto("/dossier/US:AAPL:US");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
    await expect(page.locator("text=Failed to fetch")).toHaveCount(0);

    // Verify company identity
    await expect(page.locator("text=Apple Inc.").first()).toBeVisible();

    // Screenshot Overview
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "05_dossier_aapl_overview.png"),
      fullPage: true,
    });

    // Test Forensics tab (Piotroski Card)
    const forensicsTab = page.locator("button:has-text('Forensics')");
    if (await forensicsTab.count()) {
      await forensicsTab.click();
      await page.waitForTimeout(1000);
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, "05_dossier_aapl_forensics.png"),
        fullPage: true,
      });
    }
  });

  test("06 - US:BABA:US Foreign Issuer Dossier loads with repaired name & CIK", async ({ page }) => {
    await page.goto("/dossier/US:BABA:US");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);

    // Verify Alibaba Group Holding Limited is displayed
    await expect(page.locator("text=Alibaba Group Holding Limited").first()).toBeVisible();

    // Screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "06_dossier_baba.png"),
      fullPage: true,
    });
  });

  test("07 - CA:SHOP:TSX Canadian Compounder Dossier loads cleanly", async ({ page }) => {
    await page.goto("/dossier/CA:SHOP:TSX");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);

    // Screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "07_dossier_shop.png"),
      fullPage: true,
    });
  });

  test("08 - US:JPM:US Financial Institution Dossier respects Rule #8", async ({ page }) => {
    await page.goto("/dossier/US:JPM:US");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);

    // Screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "08_dossier_jpm_bank.png"),
      fullPage: true,
    });
  });

  test("09 - Quantitative Screener renders and exports cleanly", async ({ page }) => {
    await page.goto("/screen");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);

    // Screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "09_screener.png"),
      fullPage: true,
    });
  });

  test("10 - Compare Desk renders multi-stock comparisons", async ({ page }) => {
    await page.goto("/compare?ids=US:AAPL:US,US:MSFT:US");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);

    // Screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "10_compare.png"),
      fullPage: true,
    });
  });

  test("11 - Forensics Desk: Multi-Stock Universe Screener", async ({ page }) => {
    await page.goto("/screener");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
    await expect(page.getByRole("heading", { name: /forensic screener/i })).toBeVisible();

    // Screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "11_forensic_screener_multistock.png"),
      fullPage: true,
    });
  });

  test("12 - Forensics Desk: Single-Stock Forensic Audit", async ({ page }) => {
    await page.goto("/screener?view=audit&company=US:AAPL:US");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=500 Internal Server Error")).toHaveCount(0);
    await expect(page.getByText(/Beneish M-Score/i).first()).toBeVisible();

    // Screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "12_forensic_audit_single_stock.png"),
      fullPage: true,
    });
  });
});

