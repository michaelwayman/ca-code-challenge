// Headless-browser checks for <BrandList /> (R10). Run: make browser-check
import { chromium } from "playwright";
import { readFileSync } from "node:fs";

const base = process.env.BASE_URL || "http://app:8000";
const out = process.env.OUT_DIR || "/out";
const axeSrc = readFileSync("node_modules/axe-core/axe.min.js", "utf8");

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
await page.goto(base + "/");
await page.waitForSelector("#brand-list .card");

// Tab order: record each focused element and screenshot it.
const stops = [];
await page.locator("body").click({ position: { x: 1, y: 1 } });
for (let i = 0; i < 8; i++) {
  await page.keyboard.press("Tab");
  const info = await page.evaluate(() => {
    const el = document.activeElement;
    const cs = getComputedStyle(el);
    return { tag: el.tagName, text: (el.textContent || "").slice(0, 30), outline: cs.outlineStyle + " " + cs.outlineWidth };
  });
  stops.push(info);
  if (i >= 1 && i <= 4) await page.screenshot({ path: `${out}/focus-${i}.png` });
}
console.log(JSON.stringify(stops, null, 1));

// Real-browser axe, including colour contrast.
await page.addScriptTag({ content: axeSrc });
const res = await page.evaluate(() => axe.run(document.querySelector("#brand-list")));
console.log("axe violations in browser:", res.violations.map((v) => v.id + " x" + v.nodes.length));
await browser.close();
