import { chromium } from "playwright";
import fs from "fs";

const outDir = "./screenshots";
if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();

  const routes = [
    { name: "home", url: "http://localhost:5173/" },
    { name: "dossier_aapl", url: "http://localhost:5173/c/US:AAPL:US" },
    { name: "screen", url: "http://localhost:5173/screen" },
    { name: "compare", url: "http://localhost:5173/compare?ids=US:AAPL:US,US:MSFT:US" },
    { name: "sectors", url: "http://localhost:5173/sectors" },
  ];

  for (const theme of ["dark", "light"]) {
    await page.goto("http://localhost:5173/");
    await page.evaluate((t) => {
      localStorage.setItem("investment_desk_theme", t);
      document.documentElement.setAttribute("data-theme", t);
    }, theme);

    for (const r of routes) {
      await page.goto(r.url, { waitUntil: "networkidle" });
      await page.waitForTimeout(600);

      if (r.name === "dossier_aapl") {
        await page.screenshot({ path: `${outDir}/${theme}_dossier_l1.png` });

        const l2Btn = page.locator("button:has-text('Level 2')");
        if (await l2Btn.count() > 0) {
          await l2Btn.click();
          await page.waitForTimeout(400);
          await page.screenshot({ path: `${outDir}/${theme}_dossier_l2.png` });
        }

        const l3Btn = page.locator("button:has-text('Level 3')");
        if (await l3Btn.count() > 0) {
          await l3Btn.click();
          await page.waitForTimeout(400);
          await page.screenshot({ path: `${outDir}/${theme}_dossier_l3.png` });
        }
      } else {
        await page.screenshot({ path: `${outDir}/${theme}_${r.name}.png` });
      }
    }
  }

  await browser.close();
  console.log("Screenshots captured successfully!");
}

main().catch(console.error);
