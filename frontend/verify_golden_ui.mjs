import { chromium } from "playwright";
import fs from "fs";

const outDir = "./screenshots";
if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

async function run() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 950 },
  });
  const page = await context.newPage();

  // Test 1: Home page and Typeahead search for KHC
  console.log("Testing Home & Typeahead search...");
  await page.goto("http://localhost:5173/", { waitUntil: "networkidle" });
  await page.waitForTimeout(500);

  // Type in the search input
  const searchInput = page.locator("input[placeholder*='Search']").first();
  await searchInput.click();
  await searchInput.fill("KHC");
  // Wait for debounce and suggestions
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${outDir}/typeahead_khc.png` });

  // Test 2: Navigate to KHC dossier
  console.log("Navigating to Kraft Heinz dossier...");
  await page.goto("http://localhost:5173/c/US:KHC:US", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${outDir}/khc_full_l1.png`, fullPage: true });

  // Switch to Level 2
  const l2Btn = page.locator("button:has-text('Level 2')");
  if (await l2Btn.count() > 0) {
    await l2Btn.click();
    await page.waitForTimeout(800);
    await page.screenshot({ path: `${outDir}/khc_full_l2.png`, fullPage: true });
  }

  // Switch to Level 3
  const l3Btn = page.locator("button:has-text('Level 3')");
  if (await l3Btn.count() > 0) {
    await l3Btn.click();
    await page.waitForTimeout(800);
    await page.screenshot({ path: `${outDir}/khc_full_l3.png`, fullPage: true });
  }


  // Test 3: Canadian Golden Stock CA:ABX:TSX
  console.log("Navigating to Barrick Gold dossier...");
  await page.goto("http://localhost:5173/c/CA:ABX:TSX", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${outDir}/abx_dossier_l1.png` });

  // Test 4: Apple Inc US:AAPL:US in Light Mode
  console.log("Testing Light Mode on Apple Inc...");
  await page.evaluate(() => {
    localStorage.setItem("investment_desk_theme", "light");
    document.documentElement.setAttribute("data-theme", "light");
  });
  await page.goto("http://localhost:5173/c/US:AAPL:US", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${outDir}/aapl_light_dossier_l1.png` });

  await browser.close();
  console.log("Verification screenshots captured successfully!");
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
