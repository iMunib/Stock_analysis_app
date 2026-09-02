import { expect, test } from "@playwright/test";

test("debug: does the ranked table render after load", async ({ page }) => {
  await page.goto("/sectors/Banks?currency=CAD");
  await page.waitForTimeout(5000);
  const main = await page.locator("main").innerHTML();
  console.log("HAS_RANKED=" + main.includes("Ranked companies"));
  console.log("HAS_SPINNER=" + main.includes("Loading sector"));
  console.log("HAS_TABLE=" + main.includes("<table"));
  console.log("LEN=" + main.length);
  const idx = main.indexOf("Ranked");
  if (idx >= 0) console.log("SNIPPET=" + main.slice(Math.max(0, idx - 200), idx + 300));
  else console.log("TAIL=" + main.slice(-500));
});
