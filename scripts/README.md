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

### Generate a Claude Code session screenshot

Renders a mock Claude Code terminal session and captures it as a PNG with
macOS window chrome:

```bash
node scripts/claude-code-mockup.mjs                          # built-in smello-debugger demo
node scripts/claude-code-mockup.mjs --session session.json   # custom session
node scripts/claude-code-mockup.mjs --width 900              # custom width
```

Output: `docs/assets/claude-code-screenshot.png` (transparent background).

#### Session JSON format

```json
{
  "cwd": "~/project",
  "model": "claude-sonnet-4-6",
  "project": "my-project",
  "messages": [
    { "role": "user", "text": "What's broken?" },
    { "role": "assistant", "text": "Let me check..." },
    { "role": "tool_call", "tool": "Bash", "header": "npm test", "content": "4 passed" },
    { "role": "tool_call", "tool": "Read", "header": "src/app.py", "collapsed": true },
    { "role": "tool_call", "tool": "Edit", "header": "src/app.py", "diff": { "removed": ["old line"], "added": ["new line"] } },
    { "role": "end", "text": "Sautéed for 2m 15s", "cost": "$0.05" }
  ]
}
```

Message roles: `user`, `assistant` (supports `**bold**` and `` `code` `` in text),
`tool_call` (with `tool`, `header`, optional `content`/`diff`/`collapsed`),
`end` (with `text` and optional `cost`).

## Files

| File                          | Role                                                       |
|-------------------------------|-------------------------------------------------------------|
| `demo-mockup.mjs`             | Entry point — clear, run demo, capture, generate mockup    |
| `claude-code-mockup.mjs`      | Claude Code terminal session mockup generator              |
| `lib/mockup.mjs`              | Library — `generateMockup()` and `findChrome()` exports    |
| `lib/template.mjs`            | HTML/CSS browser chrome template (supports transparent bg)  |
| `lib/claude-code-template.mjs`| HTML/CSS Claude Code terminal mock template                 |
| `lib/colors.mjs`              | Smello brand palette and light/dark chrome color tokens     |
| `assets/claude-code-icon.png` | Claude Code icon (from lobehub/lobe-icons)                  |

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
