#!/usr/bin/env node
/**
 * End-to-end demo mockup generator.
 *
 * 1. Clears all Smello data via the API
 * 2. Runs the all_in_one.py sample script to generate HTTP traffic, logs, and an exception
 * 3. Picks the first captured request so the detail panel is visible
 * 4. Calls generateMockup() to produce the final screenshot
 *
 * The default demo script intentionally raises an unhandled exception (so Smello
 * captures it), which means a non-zero exit code is expected and not treated
 * as failure.
 *
 * Usage:
 *   node scripts/demo-mockup.mjs                          # default settings
 *   node scripts/demo-mockup.mjs --dark                   # dark chrome
 *   node scripts/demo-mockup.mjs --output hero.png        # custom output
 *   node scripts/demo-mockup.mjs --script my-script.py    # custom demo script
 *
 * All mockup options (--output, --dark, --width, etc.) are supported.
 */

import { spawn } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import { generateMockup } from "./lib/mockup.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");

const SMELLO_API = process.env.SMELLO_URL || "http://localhost:5110";
const FRONTEND_URL = process.env.FRONTEND_URL || "http://localhost:5111";

// ---------------------------------------------------------------------------
// Smello API helpers
// ---------------------------------------------------------------------------

async function smelloAPI(path, { method = "GET", expect } = {}) {
  const res = await fetch(`${SMELLO_API}${path}`, { method });
  if (expect && res.status !== expect) {
    throw new Error(`${method} ${path} returned ${res.status}, expected ${expect}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

async function clearRequests() {
  await smelloAPI("/api/events", { method: "DELETE", expect: 204 });
  console.log("Cleared all Smello requests.");
}

async function waitForRequests(minCount = 1, timeoutMs = 10000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const requests = await smelloAPI(
      `/api/events?event_type=http&limit=${minCount}`,
    );
    if (requests.length >= minCount) return requests;
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`Timed out waiting for at least ${minCount} request(s) in Smello`);
}

// ---------------------------------------------------------------------------
// Demo script runner
// ---------------------------------------------------------------------------

function runDemoScript(scriptPath) {
  return new Promise((resolve) => {
    console.log(`Running ${scriptPath}...`);
    const child = spawn("uv", ["run", "python", scriptPath], {
      cwd: ROOT,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d) => (stdout += d));
    child.stderr.on("data", (d) => (stderr += d));

    // Demo scripts may intentionally raise unhandled exceptions so Smello
    // captures them — a non-zero exit code is not a failure here.
    child.on("close", (code) => {
      if (stdout) console.log(stdout.trimEnd());
      if (stderr) console.error(stderr.trimEnd());
      if (code !== 0) {
        console.log(`(demo script exited with code ${code} — continuing)`);
      }
      resolve();
    });
  });
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

const { values: args } = parseArgs({
  options: {
    // Own options
    script: { type: "string", default: resolve(ROOT, "examples/python/all_in_one.py") },
    "select-method": { type: "string", default: "POST" },
    // Mockup options (forwarded to generateMockup)
    url: { type: "string" },
    output: { type: "string", default: resolve(ROOT, "docs", "assets", "screenshot.png") },
    width: { type: "string", default: "1200" },
    height: { type: "string", default: "750" },
    dark: { type: "boolean", default: false },
    "address-bar": { type: "string", default: "localhost:5110" },
    wait: { type: "string", default: "3000" },
    help: { type: "boolean", short: "h", default: false },
  },
});

if (args.help) {
  console.log(`
Usage: node scripts/demo-mockup.mjs [options]

Demo options:
  --script <path>       Python demo script (default: examples/python/all_in_one.py)
  --select-method <m>   HTTP method to pre-select in the dashboard (default: POST).
                        Falls back to the most recent request if none match.

Mockup options:
  --url <url>           Override the screenshot URL (default: auto-detected from frontend)
  --output <path>       Output path (default: docs/assets/screenshot.png)
  --width <px>          Viewport width (default: 1400)
  --height <px>         Viewport height (default: 900)
  --dark                Dark browser chrome
  --address-bar <text>  Text in the address bar (default: localhost:5110)
  --wait <ms>           Wait time after page load (default: 3000)

Environment variables:
  SMELLO_URL            Smello API base URL (default: http://localhost:5110)
  FRONTEND_URL          Frontend URL to screenshot (default: http://localhost:5111)
`);
  process.exit(0);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  // 1. Clear
  await clearRequests();

  // 2. Run demo script
  await runDemoScript(args.script);

  // 3. Wait for captures and pick a request — prefer the configured method
  //    (POST by default) since it shows request + response bodies, then fall
  //    back to the most recent capture.
  await waitForRequests(1);
  const requests = await smelloAPI("/api/events?event_type=http&limit=50");
  const wantedMethod = args["select-method"].toUpperCase();
  const matchPrefix = `${wantedMethod} `;
  const picked =
    requests.find((r) => (r.summary || "").startsWith(matchPrefix)) || requests[0];
  console.log(`Using request ${picked.id} (${picked.summary})\n`);

  // 4. Generate mockup — URL defaults to frontend with request pre-selected
  await generateMockup({
    url: args.url || `${FRONTEND_URL}/#${picked.id}`,
    output: args.output,
    width: parseInt(args.width),
    height: parseInt(args.height),
    dark: args.dark,
    addressBar: args["address-bar"],
    wait: parseInt(args.wait),
  });
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
