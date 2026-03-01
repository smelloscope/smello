/**
 * Browser-mockup screenshot library.
 *
 * Captures a live page (or wraps an existing screenshot) in macOS-style
 * browser chrome on a branded gradient background.
 */

import puppeteer from "puppeteer-core";
import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import { buildMockupHTML } from "./template.mjs";

// ---------------------------------------------------------------------------
// Chrome discovery
// ---------------------------------------------------------------------------

const CHROME_CANDIDATES = [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium-browser",
];

export function findChrome() {
  for (const p of CHROME_CANDIDATES) {
    if (existsSync(p)) return p;
  }
  return null;
}

// ---------------------------------------------------------------------------
// Core API
// ---------------------------------------------------------------------------

/**
 * Generate a browser-mockup screenshot.
 *
 * @param {object} opts
 * @param {string}  [opts.url]         URL to screenshot (ignored if `input` is set)
 * @param {string}  [opts.input]       Path to an existing screenshot to wrap
 * @param {string}   opts.output       Output PNG path
 * @param {number}  [opts.width=1200]  Viewport width
 * @param {number}  [opts.height=750]  Viewport height
 * @param {boolean} [opts.dark=false]  Dark browser chrome
 * @param {string}  [opts.addressBar="localhost:5110"]  Address bar text
 * @param {number}  [opts.wait=2000]   Extra wait (ms) after page load
 * @param {boolean} [opts.transparent=true] Transparent background
 * @returns {Promise<string>} Resolved output path
 */
export async function generateMockup({
  url = "http://localhost:5110",
  input,
  output,
  width = 1200,
  height = 750,
  dark = false,
  addressBar = "localhost:5110",
  wait = 2000,
  transparent = true,
} = {}) {
  const executablePath = findChrome();
  if (!executablePath) {
    throw new Error("No Chrome installation found. Install Google Chrome or set CHROME_PATH.");
  }
  console.log(`Using Chrome: ${executablePath}`);

  const browser = await puppeteer.launch({ headless: true, executablePath });
  try {
    const screenshotBase64 = input
      ? readFromFile(input)
      : await captureFromUrl(browser, url, { width, height, wait });

    console.log("Rendering browser mockup...");
    const outputPath = await renderMockup(browser, screenshotBase64, {
      width,
      height,
      dark,
      addressBar,
      output,
      transparent,
    });

    console.log(`Mockup saved to ${outputPath}`);
    return outputPath;
  } finally {
    await browser.close();
  }
}

// ---------------------------------------------------------------------------
// Internals
// ---------------------------------------------------------------------------

function readFromFile(inputPath) {
  const resolved = resolve(inputPath);
  if (!existsSync(resolved)) {
    throw new Error(`Input file not found: ${resolved}`);
  }
  console.log(`Reading screenshot from ${resolved}`);
  return readFileSync(resolved).toString("base64");
}

async function captureFromUrl(browser, url, { width, height, wait }) {
  console.log(`Capturing screenshot from ${url} (${width}x${height})...`);
  const page = await browser.newPage();
  await page.setViewport({ width, height, deviceScaleFactor: 2 });
  await page.goto(url, { waitUntil: "networkidle0", timeout: 15000 });
  await new Promise((r) => setTimeout(r, wait));
  const buffer = await page.screenshot({ encoding: "base64", type: "png" });
  await page.close();
  return buffer;
}

async function renderMockup(browser, screenshotBase64, { width, height, dark, addressBar, output, transparent }) {
  const mockupPage = await browser.newPage();
  const pad = transparent ? 0 : 56;
  const mockupWidth = width + pad * 2;
  const mockupHeight = height + 44 + pad * 2; // 44px toolbar
  await mockupPage.setViewport({ width: mockupWidth, height: mockupHeight, deviceScaleFactor: 2 });

  const html = buildMockupHTML({ screenshotBase64, width, dark, addressBar, transparent });
  await mockupPage.setContent(html, { waitUntil: "load" });
  await new Promise((r) => setTimeout(r, 500));

  const outputPath = resolve(output);
  await mockupPage.screenshot({ path: outputPath, type: "png", omitBackground: true, fullPage: true });
  return outputPath;
}
