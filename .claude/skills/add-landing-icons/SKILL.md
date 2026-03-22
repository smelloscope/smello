---
name: add-landing-icons
description: >
  Find and add technology logos/icons to the Smello docs landing page.
  Use when the user wants to add a new integration card, update an existing icon,
  replace placeholder icons, or refresh the "Works With" section on the landing page.
  Also use when the user says things like "add a logo for X", "find an icon for X",
  "update the integrations section", or mentions adding a new library to the landing page.
---

# Add Landing Icons

This skill finds high-quality SVG logos for technology brands and integrates them into the Smello docs landing page.

## Where things live

- **Logo files**: `docs/assets/logos/*.svg` — white SVGs on transparent background
- **Landing page template**: `docs/overrides/home.html` — MkDocs Material custom home template
- **Integration cards**: Inside the `.integrations-grid` div in the "Works With" section

## Finding logos

Try sources in this order — earlier sources produce better, more consistent results:

### 1. Simple Icons CDN (best for well-known brands)

```
https://cdn.simpleicons.org/{slug}/white
```

Returns a white SVG ready to use. Slugs are lowercase brand names (e.g., `anthropic`, `googlecloud`, `python`). If you're unsure of the slug, check https://simpleicons.org/ or try common variations.

Some brands have been removed from Simple Icons (notably OpenAI and AWS as of 2025). If you get a 404, move to the next source.

### 2. Devicon (good for dev tools and frameworks)

```
https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/{name}/{name}-plain.svg
```

Also try `-original.svg` if `-plain.svg` doesn't exist. These SVGs have their own colors — you'll need to add `fill="#ffffff"` to the `<path>` elements to make them white.

### 3. SVG path data (for logos you know)

For well-known logos where you know the SVG path data (e.g., from having seen it before in Simple Icons or other sources), create the SVG directly:

```xml
<svg fill="#ffffff" role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <title>Brand Name</title>
  <path d="..."/>
</svg>
```

### 4. Google Favicon API (PNG fallback)

```
https://www.google.com/s2/favicons?domain={domain}&sz=128
```

Returns a 128px PNG. Use this as a last resort — SVGs are preferred because they're crisp at any size and can be colored white. Some favicons are tiny or generic (readthedocs sites often return the RTD icon, not the project's icon).

### 5. For libraries without brand logos

Some Python libraries (like `requests` or `httpx`) don't have distinctive logos. Options:
- Use the Python logo (via Simple Icons slug `python`) as a stand-in
- Create a simple text-based SVG: `<text>Hx</text>` style
- Use the parent org's logo (e.g., Encode for httpx)

## Preparing logos

All logos in this project must be:
- **SVG format** (strongly preferred over PNG)
- **White fill** (`fill="#ffffff"`) for visibility on the dark `#2A2A2E` background
- **Clean**: no embedded styles that override the fill, no unnecessary metadata

To convert a colored SVG to white, add `fill="#ffffff"` to the root `<svg>` element or to individual `<path>` elements. Remove any existing `fill` attributes that would conflict.

## Adding to the landing page

Each integration card in `docs/overrides/home.html` follows this pattern:

```html
<div class="integration-card">
  <img class="ic-icon" src="assets/logos/{name}.svg" alt="{Name}"> {Display Name}
</div>
```

Cards live inside the `.integrations-grid` div. The CSS handles sizing (22x22px) and hover effects.

## Previewing changes

```bash
# Start the docs dev server
uv run mkdocs serve -a 127.0.0.1:8111

# Template changes in overrides/ may require a server restart
pkill -f "mkdocs serve"; uv run mkdocs serve -a 127.0.0.1:8111
```

Then open http://127.0.0.1:8111 and scroll to the "Works With" section. Use Cmd+Shift+R to hard-refresh if icons look stale.

## Example workflow

Adding a "Stripe" integration card:

1. Try: `curl -sL "https://cdn.simpleicons.org/stripe/white" -o docs/assets/logos/stripe.svg`
2. Verify it's a valid SVG: `head -1 docs/assets/logos/stripe.svg` (should start with `<svg`)
3. Add the card to `.integrations-grid` in `docs/overrides/home.html`
4. Preview in browser, restart mkdocs if needed
