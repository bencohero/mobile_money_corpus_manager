import { chromium } from "playwright";
import fs from "node:fs/promises";

const baseURL = process.env.G5_BROWSER_BASE_URL ?? "http://app-test:8000";
const adminPassword = process.env.G5_BROWSER_ADMIN_PASSWORD;
const outputRoot = process.env.G5_BROWSER_OUTPUT_DIR ?? process.cwd();
if (!adminPassword) throw new Error("G5_BROWSER_ADMIN_PASSWORD is required");

const widths = [320, 360, 390, 412, 1280, 1440];
const pages = [
  ["login", "/login"],
  ["register", "/participant/register"],
  ["dashboard", "/"],
  ["participants", "/participants"],
  ["recordings", "/recordings"],
  ["record", "/record"],
  ["users", "/users"],
  ["export", "/admin/export"],
];

await fs.mkdir(`${outputRoot}/G5_1_artifacts/screenshots`, { recursive: true });
const results = [];
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.G5_BROWSER_EXECUTABLE_PATH,
  args: [
    "--use-fake-ui-for-media-stream",
    "--use-fake-device-for-media-stream",
    "--unsafely-treat-insecure-origin-as-secure=http://192.168.0.6:8000",
  ],
});

async function inspect(page, name, width) {
  const viewport = await page.evaluate(() => ({
    width: innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
    scrollHeight: document.documentElement.scrollHeight,
    bodyWidth: document.body?.scrollWidth ?? 0,
    active: document.activeElement?.tagName ?? null,
  }));
  const overflow = viewport.scrollWidth > viewport.width + 1 || viewport.bodyWidth > viewport.width + 1;
  const screenshot = `G5_1_artifacts/screenshots/${name}-${width}.png`;
  await page.screenshot({ path: `${outputRoot}/${screenshot}`, fullPage: true });
  results.push({ name, width, url: page.url(), overflow, viewport, screenshot });
  return !overflow;
}

for (const width of widths) {
  const context = await browser.newContext({
    viewport: { width, height: width < 500 ? 844 : 900 },
    permissions: ["microphone"],
    baseURL,
  });
  const page = await context.newPage();
  const browserErrors = [];
  page.on("pageerror", (error) => browserErrors.push(`pageerror: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() === "error" && !message.text().includes("favicon.ico") && !message.text().includes("403 (Forbidden)") && !message.text().includes("404 (Not Found)")) browserErrors.push(`console: ${message.text()}`);
  });
  page.on("requestfailed", (request) => browserErrors.push(`requestfailed: ${request.url()}`));

  for (const [name, path] of pages.slice(0, 2)) {
    await page.goto(path, { waitUntil: "networkidle" });
    await inspect(page, name, width);
  }

  await page.goto("/login", { waitUntil: "networkidle" });
  await page.locator("#login-username").fill("admin");
  await page.locator("#login-password").fill(adminPassword);
  await page.getByRole("button", { name: /se connecter/i }).click();
  await page.waitForLoadState("networkidle");
  if (!page.url().endsWith("/")) throw new Error(`admin login failed at ${page.url()}`);

  for (const [name, path] of pages.slice(2)) {
    await page.goto(path, { waitUntil: "networkidle" });
    await inspect(page, name, width);
  }

  const helpResponse = await page.goto("/help", { waitUntil: "networkidle" });
  results.push({ name: "participant-help-authorization", width, status: helpResponse.status(), expected: 403 });

  await page.goto("/record", { waitUntil: "networkidle" });
  await page.waitForFunction(() => Boolean(window.RecordingCapture), null, { timeout: 5000 });
  const start = page.locator("#start");
  const stop = page.locator("#stop");
  const upload = page.locator("#upload");
  let started = false;
  let stopped = false;
  let microphoneError = null;
  let uploadStatus = "not-run";
  try {
    await start.click({ timeout: 5000 });
    await page.waitForTimeout(500);
    started = await stop.isEnabled();
    if (started) await stop.click({ timeout: 5000 });
    stopped = await upload.isEnabled();
    if (width === 390 && stopped) {
      await upload.click({ timeout: 5000 });
      for (let attempt = 0; attempt < 10; attempt++) {
        await page.waitForTimeout(1000);
        uploadStatus = await page.locator("#status").textContent();
        if (!uploadStatus.includes("Envoi et normalisation")) break;
      }
    }
  } catch (error) {
    microphoneError = error.message;
  }
  results.push({ name: "simulated-microphone", width, started, stopped, microphoneError, uploadStatus, url: page.url() });

  for (let i = 0; i < 8; i++) await page.keyboard.press("Tab");
  results.push({ name: "keyboard-focus", width, active: await page.evaluate(() => document.activeElement?.tagName ?? null) });
  results.push({ name: "browser-errors", width, errors: browserErrors });
  await context.close();
}

await browser.close();
await fs.writeFile(`${outputRoot}/G5_1_artifacts/playwright-results.json`, JSON.stringify(results, null, 2));
const overflow = results.filter((item) => item.overflow);
const errors = results.filter((item) => item.name === "browser-errors" && item.errors.length);
console.log(JSON.stringify({ checks: results.length, overflow: overflow.length, browserErrorContexts: errors.length }, null, 2));
if (overflow.length || errors.length) process.exitCode = 1;
