/**
 * HTML template that wraps a screenshot in macOS-style browser chrome
 * on a branded gradient background.
 */
import { BRAND, CHROME_LIGHT, CHROME_DARK } from "./colors.mjs";

const LOCK_SVG = `<svg viewBox="0 0 24 24"><path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg>`;

/**
 * Build a full HTML page that renders the browser mockup.
 *
 * @param {object} opts
 * @param {string} opts.screenshotBase64 - Base64-encoded PNG of the inner page
 * @param {number} opts.width            - Content width in px
 * @param {boolean} opts.dark            - Use dark browser chrome
 * @param {string} opts.addressBar       - Text shown in the address bar
 * @param {boolean} opts.transparent    - Transparent background (default true)
 */
export function buildMockupHTML({
  screenshotBase64,
  width,
  dark,
  addressBar,
  transparent = true,
}) {
  const c = dark ? CHROME_DARK : CHROME_LIGHT;

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: ${
      transparent
        ? "transparent"
        : `linear-gradient(135deg, ${BRAND.navy} 0%, ${BRAND.darkBlue} 50%, ${BRAND.slateBlue} 100%)`
    };
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: ${transparent ? "0" : "48px 56px"};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }

  .browser {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: ${
      transparent
        ? "none"
        : "0 25px 80px rgba(0,0,0,0.45), 0 8px 24px rgba(0,0,0,0.2)"
    };
    width: 100%;
    max-width: ${width}px;
  }

  .toolbar {
    background: ${c.toolbar};
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .dots {
    display: flex;
    gap: 7px;
    flex-shrink: 0;
  }

  .dots span {
    width: 13px;
    height: 13px;
    border-radius: 50%;
    display: block;
  }

  .dot-close    { background: #ff5f57; }
  .dot-minimize { background: #ffbd2e; }
  .dot-maximize { background: #28c840; }

  .url-bar {
    flex: 1;
    background: ${c.urlBg};
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 13px;
    color: ${c.urlText};
    display: flex;
    align-items: center;
    gap: 8px;
    border: 1px solid ${c.border};
  }

  .lock-icon     { width: 12px; height: 12px; flex-shrink: 0; }
  .lock-icon svg { width: 12px; height: 12px; fill: ${c.lockFill}; }

  .content     { background: #fff; line-height: 0; }
  .content img { width: 100%; display: block; }
</style>
</head>
<body>
  <div class="browser">
    <div class="toolbar">
      <div class="dots">
        <span class="dot-close"></span>
        <span class="dot-minimize"></span>
        <span class="dot-maximize"></span>
      </div>
      <div class="url-bar">
        <span class="lock-icon">${LOCK_SVG}</span>
        <span>${addressBar}</span>
      </div>
    </div>
    <div class="content">
      <img src="data:image/png;base64,${screenshotBase64}" />
    </div>
  </div>
</body>
</html>`;
}
