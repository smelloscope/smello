---
name: smello-maintain-docs
description: >
  Maintain Smello documentation: add or update integration guides, edit the landing page,
  update getting-started and configuration pages, and ensure consistency across all docs.
  Use when the user says things like "add a guide for X", "update the docs", "fix the
  landing page copy", "add a new integration", or asks about documentation structure.
---

# Maintain Smello docs

This skill covers the Smello documentation site (MkDocs Material) and the conventions
that keep it consistent.

## Discovering current state

Before making changes, check what exists now. Don't rely on memorized file lists.

- `ls docs/guides/debug-*.md` for current integration guides
- `ls examples/python/` for available example scripts (link from guides when a match exists)
- Read `mkdocs.yml` for the current nav order and enabled extensions
- Read `docs/overrides/home.html` for the landing page sections and integration cards
- Read `docs/guides/index.md` for how guides are categorized
- Read an existing guide (e.g. `docs/guides/debug-requests.md`) as a reference for the current template

## Key directories

| Path | Purpose |
|------|---------|
| `docs/overrides/home.html` | Landing page (Jinja2 template extending MkDocs Material) |
| `docs/getting-started.md` | Primary onboarding page. Leads with `smello run`. |
| `docs/configuration.md` | Full config reference (params, env vars, CLI flags) |
| `docs/ai-skills.md` | Agent Skills documentation |
| `docs/guides/` | Per-library integration guides (`debug-*.md`) and index |
| `includes/` | Shared snippets (outside `docs/` so MkDocs doesn't build them as pages) |
| `mkdocs.yml` | Site config, nav order, extensions |
| `docs/assets/logos/*.svg` | White SVG logos for landing page integration cards |

## Building and previewing

```bash
uv run zensical build          # build to site/
uv run zensical serve           # dev server (port 8199)

# Or serve the built site directly
uv run zensical build && python3 -m http.server 8201 --directory site
```

Do NOT use `mkdocs build` or `mkdocs serve` directly. This project uses `zensical` as its build tool.

## Guide template

Every integration guide in `docs/guides/` follows this structure. Read an existing guide to confirm the current conventions before writing a new one.

```markdown
# Debug {library} with Smello

{One paragraph: what the library does, why debugging it is hard, and that Smello captures it automatically.}

## Setup

{pip install + smello-server + smello run command}

> **Example script**: [`{script}.py`](https://github.com/smelloscope/smello/blob/main/examples/python/{script}.py)

## Scenario: debugging {specific problem}

{Description of a realistic debugging problem.}

{Code snippet showing the problem.}

### Debug in the dashboard

{Open the Smello dashboard. Bullet list of what to look at, with bold panel names:}

![Smello dashboard showing captured {library} requests](assets/debug-{name}-dashboard.png)

- **Request body**: {what to check}
- **Response body**: {what to check}

### Debug with an AI agent

If you use [Claude Code](https://claude.ai/code) or another AI coding tool, the `/smello-debugger` skill can query captured events and cross-reference them with your source code. Install it once:

\`\`\`bash
npx skills add smelloscope/smello --skill smello-debugger
\`\`\`

Then ask your agent:

\`\`\`
/smello-debugger
{Natural language question matching the scenario}
\`\`\`

![Claude Code session using smello-debugger to diagnose the issue](assets/debug-{name}-claude.png)

The skill is also invoked automatically when your agent recognizes a debugging question, but calling `/smello-debugger` explicitly gives the best results. See [AI Agent Skills](../ai-skills.md) for compatible tools.

## Tips

- **{Topic}**: {Practical tip}

--8<-- "includes/guide-next-steps.md"
```

### Example link

Add an example link in Setup only if a matching script exists in `examples/python/`. Check the directory to find matches. Don't assume which scripts exist.

### Snippet include

Every guide ends with a shared CTA via `pymdownx.snippets`. The include file lives in `includes/` (outside `docs/`). Check what includes exist before adding new ones.

## Adding a new integration guide

1. Read an existing guide to confirm the current template
2. Create `docs/guides/debug-{name}.md` following the template
3. Add it to `docs/guides/index.md` under the appropriate category
4. Add it to the `nav:` section in `mkdocs.yml` under Guides
5. Check `examples/python/` for a matching example script to link
6. If there's a landing page card, add it to `docs/overrides/home.html` in the `.integrations-grid` div (use the `smello-add-landing-icons` skill for the logo)
7. Build and verify: `uv run zensical build`

## Landing page conventions

The landing page (`docs/overrides/home.html`) is a Jinja2 template. Read it to see the current sections. Key conventions:

- Integration cards are `<a>` tags with `href="guides/debug-{name}/"` linking to the corresponding guide
- Logos are white SVGs in `docs/assets/logos/`
- The "How it works" section leads with `smello run`, not `smello.init()`

## Screenshots

Every guide should include screenshots for both debugging workflows:

1. **Dashboard screenshot** after the "Debug in the dashboard" heading
2. **Claude Code screenshot** after the `/smello-debugger` example

Use the `/smello-screenshot-maker` skill to generate them. Screenshots go in `docs/guides/assets/`
and session JSON files live alongside them. Reference with relative paths:

```markdown
![Smello dashboard showing captured requests](assets/debug-{name}-dashboard.png)
![Claude Code session using smello-debugger](assets/debug-{name}-claude.png)
```

When creating or updating a guide, generate both screenshots as part of the work.
See `/smello-screenshot-maker` for the full workflow (two-step approach for dashboard,
`--session` flag for Claude Code).

## Key messaging

- `smello run` is the primary integration path. Always lead with it.
- `smello.init()` is the secondary/fallback approach. Mention it after `smello run`.
- FastAPI middleware is the one integration that always requires a code change.
- Smello captures HTTP traffic, logs, and exceptions. Not just HTTP.
- Zero code changes (with `smello run`). Zero dependencies (client SDK).

## Writing style

Follow the project's writing guidelines (`/writing` skill). Key rules:

- **No em dashes**. Use periods, commas, or colons instead.
- **Sentence case headings**: capitalize first word and proper nouns only.
- **Active voice**: "Smello captures X" not "X is captured by Smello."
- **No avoid-list words**: delve, leverage, seamless, robust, enhance, utilize, crucial, pivotal, etc.
- **No marketing superlatives**: powerful, cutting-edge, revolutionary.
- **Colons over em dashes** in bold-label bullets: `**Label**: explanation`
- **No empty -ing phrases**: "making it easy to..." becomes "so you can..."
- **Be direct**: say what something does, not what it "helps you to" or "allows you to" do.
