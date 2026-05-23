#!/usr/bin/env node
/**
 * Generate a screenshot of a mock Claude Code terminal session.
 *
 * Renders an HTML page that emulates the Claude Code CLI, then captures
 * it with Puppeteer and wraps it in macOS-style window chrome.
 *
 * Usage:
 *   node scripts/claude-code-mockup.mjs                           # default demo
 *   node scripts/claude-code-mockup.mjs --session session.json    # custom session
 *   node scripts/claude-code-mockup.mjs --dark                    # dark chrome
 *   node scripts/claude-code-mockup.mjs --width 900 --height 600  # custom size
 *
 * Session JSON format:
 *   {
 *     "cwd": "~/my-project",
 *     "model": "claude-sonnet-4-6",
 *     "project": "my-project",
 *     "messages": [
 *       { "role": "user", "text": "What's broken?" },
 *       { "role": "assistant", "text": "Let me check..." },
 *       { "role": "tool_call", "tool": "Bash", "header": "npm test", "content": "4 passed" },
 *       { "role": "tool_call", "tool": "Read", "header": "src/app.py", "collapsed": true },
 *       { "role": "tool_call", "tool": "Edit", "header": "src/app.py", "diff": { "removed": ["old"], "added": ["new"] } },
 *       { "role": "end", "text": "Sautéed for 2m 15s", "cost": "$0.05" }
 *     ]
 *   }
 */

import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import puppeteer from "puppeteer-core";
import { buildClaudeCodeHTML } from "./lib/claude-code-template.mjs";
import { findChrome } from "./lib/mockup.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");

// ---------------------------------------------------------------------------
// Default demo session: using the smello skill
// ---------------------------------------------------------------------------

const DEFAULT_SESSION = {
  cwd: "~/acme-api",
  model: "claude-sonnet-4-6",
  project: "acme-api",
  messages: [
    {
      role: "user",
      text: "The /api/orders endpoint is returning 500 errors. Debug it?",
    },
    {
      role: "tool_call",
      tool: "Skill",
      header: "smello",
      collapsed: true,
    },
    {
      role: "tool_call",
      tool: "Bash",
      header: "curl -s localhost:5110/api/events | jq '[.[] | select(.summary | startswith(\"POST /api/orders\"))]'",
      collapsed: true,
    },
    {
      role: "assistant",
      text: "Found the failing request in Smello: `POST /api/orders → 500`. The response body shows an \`IntegrityError\` — null value in column `warehouse_id`.",
    },
    {
      role: "tool_call",
      tool: "Edit",
      header: "routes/orders.py",
      diff: {
        removed: [
          "    order = Order(product_id=data.product_id, qty=data.qty)",
        ],
        added: [
          "    warehouse = await Inventory.get_warehouse(data.product_id)",
          "    order = Order(product_id=data.product_id, qty=data.qty,",
          "                  warehouse_id=warehouse.id)",
        ],
      },
    },
    {
      role: "tool_call",
      tool: "Bash",
      header: "uv run pytest tests/test_orders.py -x -q",
      content: "4 passed in 0.82s",
    },
    {
      role: "end",
      text: "Sautéed for 1m 12s",
    },
  ],
};

// ---------------------------------------------------------------------------
// Icon loader
// ---------------------------------------------------------------------------

function loadIcon() {
  const iconPath = resolve(__dirname, "assets", "claude-code-icon.png");
  if (existsSync(iconPath)) {
    return readFileSync(iconPath).toString("base64");
  }
  return "";
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

const { values: args } = parseArgs({
  options: {
    session: { type: "string" },
    output: {
      type: "string",
      default: resolve(ROOT, "docs", "assets", "claude-code-screenshot.png"),
    },
    width: { type: "string", default: "860" },
    height: { type: "string", default: "auto" },
    dark: { type: "boolean", default: true },
    "no-input": { type: "boolean", default: false },
    wait: { type: "string", default: "1000" },
    help: { type: "boolean", short: "h", default: false },
  },
});

if (args.help) {
  console.log(`
Usage: node scripts/claude-code-mockup.mjs [options]

Options:
  --session <path>       Path to a session JSON file (default: built-in demo)
  --output <path>        Output PNG path (default: docs/assets/claude-code-screenshot.png)
  --width <px>           Terminal width (default: 860)
  --height <px|"auto">   Terminal height — "auto" fits content (default: auto)
  --dark                 Dark window chrome (default: true)
  --wait <ms>            Wait before capture for fonts to load (default: 1000)
  -h, --help             Show this help

Session JSON format:
  {
    "cwd": "~/project",
    "model": "claude-sonnet-4-6",
    "project": "my-project",
    "messages": [
      { "role": "user", "text": "..." },
      { "role": "assistant", "text": "..." },
      { "role": "tool_call", "tool": "Bash", "header": "npm test", "content": "output" },
      { "role": "tool_call", "tool": "Read", "header": "file.py", "collapsed": true },
      { "role": "tool_call", "tool": "Edit", "header": "file.py", "diff": { "removed": [...], "added": [...] } },
      { "role": "end", "text": "Sautéed for 2m 15s", "cost": "$0.05" }
    ]
  }
`);
  process.exit(0);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const executablePath = findChrome();
  if (!executablePath) {
    throw new Error("No Chrome installation found.");
  }
  console.log(`Using Chrome: ${executablePath}`);

  // Load session
  let session = DEFAULT_SESSION;
  if (args.session) {
    const sessionPath = resolve(args.session);
    session = JSON.parse(readFileSync(sessionPath, "utf-8"));
    console.log(`Loaded session from ${sessionPath}`);
  } else {
    console.log("Using built-in demo session (smello)");
  }

  const width = parseInt(args.width);
  const iconBase64 = loadIcon();

  // Build the Claude Code HTML
  const html = buildClaudeCodeHTML({
    messages: session.messages,
    width,
    cwd: session.cwd || "~/project",
    iconBase64,
    model: session.model || "claude-sonnet-4-6",
    project: session.project || "",
    showInput: !args["no-input"],
  });

  const browser = await puppeteer.launch({ headless: true, executablePath });

  try {
    // Render the terminal HTML and capture it
    console.log("Rendering Claude Code session...");
    const page = await browser.newPage();
    await page.setViewport({ width, height: 800, deviceScaleFactor: 2 });
    await page.setContent(html, { waitUntil: "networkidle0" });
    await new Promise((r) => setTimeout(r, parseInt(args.wait)));

    // Measure actual content height if auto
    let captureHeight;
    if (args.height === "auto") {
      captureHeight = await page.evaluate(() => document.body.scrollHeight);
    } else {
      captureHeight = parseInt(args.height);
    }

    await page.setViewport({ width, height: captureHeight, deviceScaleFactor: 2 });
    await new Promise((r) => setTimeout(r, 200));

    const screenshotBase64 = await page.screenshot({
      encoding: "base64",
      type: "png",
      clip: { x: 0, y: 0, width, height: captureHeight },
    });
    await page.close();

    // Wrap in macOS chrome
    console.log("Adding window chrome...");
    const mockupPage = await browser.newPage();
    const mockupWidth = width;
    const mockupHeight = captureHeight + 44; // 44px for toolbar
    await mockupPage.setViewport({
      width: mockupWidth,
      height: mockupHeight,
      deviceScaleFactor: 2,
    });

    const mockupHtml = buildTerminalMockupHTML({
      screenshotBase64,
      width,
      height: captureHeight,
      dark: args.dark,
      title: session.project
        ? `Claude Code — ${session.project}`
        : "Claude Code",
    });

    await mockupPage.setContent(mockupHtml, { waitUntil: "load" });
    await new Promise((r) => setTimeout(r, 300));

    const outputPath = resolve(args.output);
    await mockupPage.screenshot({
      path: outputPath,
      type: "png",
      omitBackground: true,
      fullPage: true,
    });

    console.log(`Screenshot saved to ${outputPath}`);
    return outputPath;
  } finally {
    await browser.close();
  }
}

// ---------------------------------------------------------------------------
// Terminal-style window chrome (no address bar, just title)
// ---------------------------------------------------------------------------

function buildTerminalMockupHTML({ screenshotBase64, width, height, dark, title }) {
  const toolbarBg = dark ? "#2d2d2d" : "#e8e8e8";
  const titleColor = dark ? "#ccc" : "#555";

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: transparent;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }

  .window {
    border-radius: 10px;
    overflow: hidden;
    width: ${width}px;
    box-shadow: 0 0 0 0.5px rgba(255,255,255,0.1);
  }

  .titlebar {
    background: ${toolbarBg};
    padding: 11px 16px;
    display: flex;
    align-items: center;
    position: relative;
  }

  .dots {
    display: flex;
    gap: 7px;
    flex-shrink: 0;
    z-index: 1;
  }

  .dots span {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: block;
  }

  .dot-close    { background: #ff5f57; }
  .dot-minimize { background: #ffbd2e; }
  .dot-maximize { background: #28c840; }

  .title-text {
    position: absolute;
    left: 0;
    right: 0;
    text-align: center;
    font-size: 13px;
    color: ${titleColor};
    pointer-events: none;
  }

  .content {
    line-height: 0;
  }

  .content img {
    width: 100%;
    display: block;
  }
</style>
</head>
<body>
  <div class="window">
    <div class="titlebar">
      <div class="dots">
        <span class="dot-close"></span>
        <span class="dot-minimize"></span>
        <span class="dot-maximize"></span>
      </div>
      <span class="title-text">${title}</span>
    </div>
    <div class="content">
      <img src="data:image/png;base64,${screenshotBase64}" />
    </div>
  </div>
</body>
</html>`;
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
