import { chromium } from "playwright";
import fs from "fs";

const outDir = "./screenshots/personas";
if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

async function run() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 950 },
  });
  const page = await context.newPage();

  console.log("=== PERSONA A: Retail Investor (60s Executive Cockpit) ===");
  // Step 1: Home page and Typeahead with Russell 1000 & Microcap Badges
  await page.goto("http://localhost:5173/", { waitUntil: "networkidle" });
  await page.waitForTimeout(600);

  const searchInput = page.locator("input[placeholder*='Search']").first();
  await searchInput.click();
  await searchInput.fill("CELH");
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${outDir}/persona_a_typeahead_russell1000.png` });

  // Step 2: Navigate to CELH Level 1 Cockpit
  await page.goto("http://localhost:5173/c/US:CELH:US", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${outDir}/persona_a_celh_cockpit.png`, fullPage: true });

  console.log("=== PERSONA B: Value Hunter (Buffett Owner Earnings & Buyback Deficit) ===");
  // AutoZone (AZO) has negative book equity from aggressive share repurchases
  await page.goto("http://localhost:5173/c/US:AZO:US", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${outDir}/persona_b_azo_buyback_deficit_l1.png` });

  // Switch to Level 2 Flight Deck for Buffett Owner Earnings and Cash Flow Waterfall
  const l2Btn = page.locator("button:has-text('Level 2')");
  if (await l2Btn.count() > 0) {
    await l2Btn.click();
    await page.waitForTimeout(800);
    await page.screenshot({ path: `${outDir}/persona_b_azo_flight_deck.png`, fullPage: true });
  }

  console.log("=== PERSONA C: Forensic Risk Analyst (Beneish, Altman Z, Penman) ===");
  await page.goto("http://localhost:5173/c/US:PLTR:US", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  const l3Btn = page.locator("button:has-text('Level 3')");
  if (await l3Btn.count() > 0) {
    await l3Btn.click();
    await page.waitForTimeout(800);
    await page.screenshot({ path: `${outDir}/persona_c_pltr_engine_room.png`, fullPage: true });
  }

  console.log("=== PERSONA D: Canadian / Cross-Border Allocator ===");
  // Bombardier CA:BBD.B:TSX
  await page.goto("http://localhost:5173/c/CA:BBD.B:TSX", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${outDir}/persona_d_bombardier_tsx.png`, fullPage: true });

  // Celestica CA:CLS:TSX
  await page.goto("http://localhost:5173/c/CA:CLS:TSX", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${outDir}/persona_d_celestica_cad_isolated.png` });

  // Screener preset test
  await page.goto("http://localhost:5173/screen", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${outDir}/persona_d_screener.png`, fullPage: true });

  await browser.close();
  console.log("Persona testing complete! Screenshots saved to screenshots/personas/");
}

run().catch((err) => {
  console.error("Error during persona verification:", err);
  process.exit(1);
});
