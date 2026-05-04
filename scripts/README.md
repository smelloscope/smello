# scripts/

Tooling for generating browser-mockup screenshots of the Smello dashboard.

## Quick start

```bash
cd scripts && npm install   # one-time: installs puppeteer-core (~3MB, uses system Chrome)
```

### Generate a demo screenshot (recommended)

Clears Smello, runs the `all_in_one.py` demo to populate HTTP traffic, log
events, and an unhandled exception, then captures a mockup with the first
request selected:

```bash
# Requires: smello-server on :5110 and frontend dev server on :5111
node scripts/demo-mockup.mjs
```

Output: `docs/assets/screenshot.png` (transparent background, ready for the landing page).

### Options

```bash
node scripts/demo-mockup.mjs --dark                   # dark browser chrome
node scripts/demo-mockup.mjs --output hero.png         # custom output path
node scripts/demo-mockup.mjs --width 1400 --height 900 # custom viewport
node scripts/demo-mockup.mjs --script my-demo.py       # custom Python demo script
node scripts/demo-mockup.mjs --transparent false        # with branded gradient background
```

### Environment variables

| Variable       | Default                  | Description                     |
|----------------|--------------------------|---------------------------------|
| `SMELLO_URL`   | `http://localhost:5110`  | Smello API base URL             |
| `FRONTEND_URL` | `http://localhost:5111`  | Frontend URL to screenshot      |

## Files

| File                | Role                                                       |
|---------------------|------------------------------------------------------------|
| `demo-mockup.mjs`   | Entry point — clear, run demo, capture, generate mockup   |
| `lib/mockup.mjs`    | Library — `generateMockup()` and `findChrome()` exports   |
| `lib/template.mjs`  | HTML/CSS browser chrome template (supports transparent bg) |
| `lib/colors.mjs`    | Smello brand palette and light/dark chrome color tokens    |

## How it works

1. **Clear** — `DELETE /api/events` removes all captured traffic.
2. **Demo** — Runs `examples/python/all_in_one.py` (or a custom script) which
   sends HTTP requests, emits log events, and raises an unhandled exception
   through the Smello client SDK. Non-zero exit codes from the demo script are
   tolerated, since the default script intentionally raises.
3. **Pick** — Polls `GET /api/events?event_type=http` until captures arrive, takes
   the first request ID for deep-linking via URL hash.
4. **Capture** — Puppeteer (using system Chrome) opens the frontend with the
   request pre-selected and takes a 2x retina screenshot.
5. **Wrap** — A second Puppeteer page renders the screenshot inside an HTML/CSS
   browser chrome template (macOS traffic lights, address bar, rounded corners).
6. **Save** — The composite is saved as a PNG. When `transparent=true` (default),
   the background is transparent so it blends into any page background.
