---
name: smello-screenshot-maker
description: >
  Generate or regenerate screenshots for the Smello landing page and docs.
  Covers both the dashboard screenshot (Smello UI) and the Claude Code session
  screenshot (mock terminal). Use when the user says "update the screenshot",
  "regenerate screenshots", "take a new screenshot", "the screenshot is outdated",
  or after any UI or demo session changes. Also use when the user wants to create
  a new Claude Code session mockup or change the demo content shown in it.
---

# Screenshot Maker

Generate screenshots for the Smello landing page and integration guides. Two types exist.
Both support `--output <path>` to write to any location (guides, README, etc.).

All scripts run from the `scripts/` directory (where `node_modules` lives). Use absolute
paths for `--output` since it resolves relative to cwd, not the project root.

```bash
cd scripts && npm install   # one-time
```

## 1. Dashboard screenshot (Smello UI)

Captures the live Smello frontend with demo data populated.

**Prerequisites**: smello-server running on :5110, frontend dev server on :5111.

### Quick: landing page screenshot

```bash
node scripts/demo-mockup.mjs
```

Output: `docs/assets/screenshot.png`

This clears all Smello data, runs the demo script (`examples/python/all_in_one.py`),
picks the first POST request, and captures the frontend with that request selected.

Options: `--dark`, `--width <px>`, `--height <px>`, `--output <path>`,
`--script <path>` (custom demo), `--select-method <method>`.

### Guide-specific: two-step approach

`demo-mockup.mjs` always clears data and re-runs the demo, so the `--url` flag
with a pre-known request ID won't work (IDs change after clear). For guide screenshots
where you need a specific request selected, use the library directly:

```bash
# Step 1: Clear, run demo, find the request you want
curl -s -X DELETE http://localhost:5110/api/events
uv run python examples/python/basic_requests.py
sleep 2
# List captured requests and pick the right ID
curl -s "http://localhost:5110/api/events?event_type=http" | python3 -c "
import sys, json
[print(e['id'], e['summary']) for e in json.load(sys.stdin)]
"
```

```bash
# Step 2: Generate mockup with that request selected
node -e "
import { generateMockup } from './lib/mockup.mjs';
await generateMockup({
  url: 'http://localhost:5111/#REQUEST_ID_HERE',
  output: '/absolute/path/to/output.png',
  width: 1000,
  height: 620,
  wait: 3000,
});
"
```

The `--script` flag path resolves from the project root, not from `scripts/`.

Both screenshots use transparent backgrounds so they blend into any page background.

## 2. Claude Code session screenshot

Renders a mock Claude Code terminal and captures it as a PNG with macOS window chrome.
No running servers needed.

```bash
node scripts/claude-code-mockup.mjs --no-input
```

Output: `docs/assets/claude-code-screenshot.png`

Options: `--session <path>` (custom session JSON), `--width <px>`, `--output <path>`,
`--dark` / `--no-dark`, `--no-input` (hide the input prompt), `--wait <ms>`.

### Editing the demo session

The built-in demo session is defined in `scripts/claude-code-mockup.mjs` as `DEFAULT_SESSION`.
Edit the `messages` array directly, or pass `--session custom.json` for a separate file.

### Session JSON format

```json
{
  "cwd": "~/project",
  "model": "claude-sonnet-4-6",
  "project": "my-project",
  "messages": [
    { "role": "user", "text": "user prompt" },
    { "role": "assistant", "text": "response with `code` and **bold**" },
    { "role": "tool_call", "tool": "Bash", "header": "npm test", "content": "output text" },
    { "role": "tool_call", "tool": "Read", "header": "file.py", "collapsed": true },
    { "role": "tool_call", "tool": "Edit", "header": "file.py", "diff": {
        "removed": ["old line"],
        "added": ["new line"]
    }},
    { "role": "end", "text": "Sautéed for 2m 15s" }
  ]
}
```

Message roles:
- `user`: gray background, `>` marker. Text is plain.
- `assistant`: white circle. Text supports `**bold**` and `` `code` `` (rendered blue).
- `tool_call`: green circle. `tool` is the tool name (bold), `header` is the summary text.
  - `content`: optional output text shown in a code block.
  - `collapsed`: hides the output, shows a `▶` indicator.
  - `diff`: shows red/green diff lines instead of content. `{ removed: [...], added: [...] }`.
- `end`: muted footer with `✻` icon. Optional `cost` field.

## Usage in guides

Guide screenshots go in `docs/guides/assets/`. Session JSON files live alongside
the screenshots for easy regeneration.

```bash
# Dashboard screenshot for a guide (two-step, see above)
# Claude Code session for a guide
node scripts/claude-code-mockup.mjs --no-input \
  --session /absolute/path/to/docs/guides/assets/debug-requests-session.json \
  --output /absolute/path/to/docs/guides/assets/debug-requests-claude.png
```

In guide markdown, reference screenshots with a relative path:

```markdown
![Smello dashboard showing captured requests](assets/debug-requests-dashboard.png)
![Claude Code session debugging a 401 error](assets/debug-requests-claude.png)
```

## Where screenshots currently appear

- **Landing page** (`docs/overrides/home.html`):
  - Dashboard screenshot in hero section (`max-width: 900px`)
  - Claude Code screenshot in "AI Agent Skills" section (`max-width: 700px`)
- **Integration guides** (`docs/guides/debug-*.md`):
  - Dashboard screenshot after "Debug in the dashboard"
  - Claude Code screenshot after the `/smello-debugger` example

## Key files

| File | Purpose |
|------|---------|
| `scripts/demo-mockup.mjs` | Dashboard screenshot CLI (clear + demo + capture) |
| `scripts/claude-code-mockup.mjs` | Claude Code session CLI + default session |
| `scripts/lib/mockup.mjs` | Puppeteer screenshot library (`generateMockup`, `findChrome`) |
| `scripts/lib/template.mjs` | macOS browser chrome HTML wrapper |
| `scripts/lib/claude-code-template.mjs` | Claude Code terminal mock HTML template |
| `scripts/lib/colors.mjs` | Brand color palette |
| `scripts/assets/claude-code-icon.png` | Claude Code icon shown in the header |
