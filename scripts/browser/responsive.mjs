// Responsive checks for <BrandList /> (R11). Run via make browser-check.
import { chromium } from "playwright";

const base = process.env.BASE_URL || "http://app:8000";
const out = process.env.OUT_DIR || "/out";
const browser = await chromium.launch();
let failed = false;
const assert = (ok, msg) => { console.log((ok ? "PASS " : "FAIL ") + msg); if (!ok) failed = true; };

async function open(width, height) {
  const page = await browser.newPage({ viewport: { width, height } });
  await page.goto(base + "/");
  await page.waitForSelector("#brand-list .card");
  return page;
}

// 375px: single column, no horizontal scroll, controls fit, touch targets >= 44px.
let page = await open(375, 800);
const m = await page.evaluate(() => {
  const cards = [...document.querySelectorAll("#brand-list .card")].map((c) => c.getBoundingClientRect());
  const lefts = new Set(cards.map((r) => Math.round(r.left)));
  const controls = [...document.querySelectorAll(".brand-list-controls select, .brand-list-controls label")].map((e) => e.getBoundingClientRect());
  const targets = [...document.querySelectorAll(".brand-list-controls select, .brand-list-controls button")].map((e) => {
    const r = e.getBoundingClientRect();
    return { tag: e.tagName, text: (e.textContent || "").slice(0, 20), w: r.width, h: r.height };
  });
  return {
    cardCount: cards.length, columns: lefts.size,
    scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth,
    controlsMaxRight: Math.max(...controls.map((r) => r.right)),
    targets,
  };
});
console.log(JSON.stringify(m));
assert(m.cardCount > 1, `cards rendered (${m.cardCount})`);
assert(m.columns === 1, `375px: one column (${m.columns})`);
assert(m.scrollW <= m.clientW, `375px: no horizontal scroll (${m.scrollW} <= ${m.clientW})`);
assert(m.controlsMaxRight <= m.clientW, `375px: controls fit (${m.controlsMaxRight} <= ${m.clientW})`);
const small = m.targets.filter((t) => t.h < 44);
assert(small.length === 0, `375px: control touch targets >= 44px tall (${small.length} too small: ${JSON.stringify(small)})`);
await page.screenshot({ path: `${out}/responsive-375.png`, fullPage: true });
await page.close();

// Error-state retry button is also a control: >= 44px at 375px.
page = await browser.newPage({ viewport: { width: 375, height: 800 } });
await page.route("**/api/brands/**", (r) => r.abort());
await page.goto(base + "/");
await page.waitForSelector(".brand-list-error button");
const bh = (await page.locator(".brand-list-error button").boundingBox()).height;
assert(bh >= 44, `375px: retry button >= 44px tall (${bh})`);
await page.close();

// 1280px: multi-column inside the container.
page = await open(1280, 900);
const d = await page.evaluate(() => {
  const cards = [...document.querySelectorAll("#brand-list .card")].map((c) => c.getBoundingClientRect());
  const cont = document.querySelector("#brand-list").closest(".container")?.getBoundingClientRect();
  return {
    columns: new Set(cards.map((r) => Math.round(r.left))).size,
    minLeft: Math.min(...cards.map((r) => r.left)), maxRight: Math.max(...cards.map((r) => r.right)),
    cont: cont && { left: cont.left, right: cont.right },
    scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth,
  };
});
console.log(JSON.stringify(d));
assert(d.columns >= 2, `1280px: multi-column (${d.columns})`);
assert(d.cont && d.minLeft >= d.cont.left - 1 && d.maxRight <= d.cont.right + 1, "1280px: cards within container");
assert(d.scrollW <= d.clientW, "1280px: no horizontal scroll");
await page.screenshot({ path: `${out}/responsive-1280.png`, fullPage: true });
await browser.close();
process.exit(failed ? 1 : 0);
