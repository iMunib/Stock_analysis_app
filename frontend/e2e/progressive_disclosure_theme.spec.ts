import { test, expect } from "@playwright/test";

test.describe("Enterprise UI, Dual-Theme & 3-Tier Progressive Disclosure", () => {
  test("ThemeToggle persists light and dark mode across reloads", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Initially should be dark or undefined theme attribute
    const themeBtn = page.getByRole("button", { name: /switch to light mode/i });
    await expect(themeBtn).toBeVisible();

    // Toggle to light mode
    await themeBtn.click();

    // Verify data-theme attribute on html element
    const themeAttr = await page.getAttribute("html", "data-theme");
    expect(themeAttr).toBe("light");

    // Verify localStorage persistence
    const stored = await page.evaluate(() => localStorage.getItem("investment_desk_theme"));
    expect(stored).toBe("light");

    // Reload page and verify light mode remains active (no FOUC)
    await page.reload();
    await page.waitForLoadState("networkidle");

    const reloadedTheme = await page.getAttribute("html", "data-theme");
    expect(reloadedTheme).toBe("light");

    // Toggle back to dark mode
    const darkBtn = page.getByRole("button", { name: /switch to dark mode/i });
    await expect(darkBtn).toBeVisible();
    await darkBtn.click();

    const finalTheme = await page.getAttribute("html", "data-theme");
    expect(finalTheme).toBe("dark");
  });

  test("Dossier 3-tier progressive disclosure: Level 1 Cockpit, Level 2 Flight Deck, Level 3 Engine Room", async ({
    page,
  }) => {
    await page.goto("/c/US:AAPL:US");
    await page.waitForLoadState("networkidle");

    // --- LEVEL 1: 60-SECOND EXECUTIVE COCKPIT (Default) ---
    await expect(page.getByRole("button", { name: /Level 1: 60s Cockpit/i })).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByText(/Level 1: 60-Second Executive Cockpit/i)).toBeVisible();
    await expect(page.getByText(/Bottom-Line Safety Verdict:/i)).toBeVisible();

    // Check 3 Traffic Light Tiles
    await expect(page.getByText(/1\. Business Moat & Quality/i)).toBeVisible();
    await expect(page.getByText(/2\. Financial Safety & Solvency/i)).toBeVisible();
    await expect(page.getByText(/3\. Valuation & Growth Hurdle/i)).toBeVisible();

    // Check Reverse DCF rule box & decision bullets
    await expect(page.getByText(/The Market's Expectation \(Reverse DCF Rule\)/i)).toBeVisible();
    await expect(page.getByText(/Plain-English Decision Summary/i)).toBeVisible();
    await expect(page.getByText(/Why Buy \(Core Strengths\)/i)).toBeVisible();
    await expect(page.getByText(/Key Risk to Watch/i)).toBeVisible();
    await expect(page.getByText(/Index Opportunity Cost/i)).toBeVisible();

    // --- LEVEL 2: 5-MINUTE FLIGHT DECK ---
    const level2Btn = page.getByRole("button", { name: /Level 2: Flight Deck/i });
    await level2Btn.click();

    await expect(page.getByText(/Level 2: 5-Minute Flight Deck/i)).toBeVisible();
    await expect(page.getByText(/4-Pillar Research Radar/i)).toBeVisible();
    await expect(page.getByText(/Peter Lynch Archetype & Valuation/i)).toBeVisible();
    await expect(page.getByText(/Buffett Owner Earnings/i)).toBeVisible();
    await expect(page.getByText(/True Shareholder Yield/i).first()).toBeVisible();
    await expect(page.getByText(/Less: SBC Dilution/i)).toBeVisible();
    await expect(page.getByText(/Ittelson Cash Flow Waterfall/i)).toBeVisible();

    // --- LEVEL 3: INSTITUTIONAL ENGINE ROOM ---
    const level3Btn = page.getByRole("button", { name: /Level 3: Engine Room/i });
    await level3Btn.click();

    await expect(page.getByText(/Level 3: Institutional Engine Room/i)).toBeVisible();
    await expect(page.getByText(/Beneish 8-Variable Forensic Matrix/i)).toBeVisible();
    await expect(page.getByText("DSRI")).toBeVisible();
    await expect(page.getByText("TATA")).toBeVisible();
    await expect(page.getByText(/Stephen Penman Reformulation/i)).toBeVisible();
    await expect(page.getByText(/FLEV \(Debt Leverage Multiplier\)/i)).toBeVisible();
    await expect(page.getByText(/Edward Altman Distress & Solvency Suite/i)).toBeVisible();
    await expect(page.getByText(/Martin Fridson Reality Spread/i)).toBeVisible();

    // Switch back to Level 1
    const level1Btn = page.getByRole("button", { name: /Level 1: 60s Cockpit/i });
    await level1Btn.click();
    await expect(page.getByText(/Level 1: 60-Second Executive Cockpit/i)).toBeVisible();
  });
});
