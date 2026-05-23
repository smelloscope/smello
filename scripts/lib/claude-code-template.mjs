/**
 * HTML template that renders a mock Claude Code terminal session.
 *
 * The output is a self-contained HTML page designed to be screenshotted
 * by Puppeteer. It emulates the Claude Code CLI look and feel.
 */

/**
 * Build a full HTML page that renders a Claude Code terminal mock.
 *
 * @param {object} opts
 * @param {Array}  opts.messages     - Array of message objects (see below)
 * @param {number} opts.width        - Viewport width in px
 * @param {string} [opts.cwd]       - Working directory shown in the input prompt
 * @param {boolean} [opts.showInput] - Show the input prompt at the bottom (default true)
 * @param {string} [opts.iconBase64] - Base64 Claude Code icon (PNG/SVG)
 * @param {string} [opts.model]      - Model name shown in header
 * @param {string} [opts.project]    - Project name shown in header
 *
 * Message types:
 *   { role: "user",        text: "..." }
 *   { role: "assistant",   text: "..." }
 *   { role: "tool_call",   tool: "Bash", header: "npm test", content: "..." }
 *   { role: "tool_call",   tool: "Read", header: "src/app.py", collapsed: true }
 *   { role: "tool_call",   tool: "Edit", header: "src/app.py", diff: { removed: [...], added: [...] } }
 *   { role: "end",         text: "Sautéed for 5m 37s", cost: "$0.12" }
 */
export function buildClaudeCodeHTML({
  messages = [],
  width = 800,
  cwd = "~/project",
  iconBase64 = "",
  model = "claude-sonnet-4-6",
  project = "",
  showInput = true,
}) {
  const iconSrc = iconBase64
    ? `data:image/png;base64,${iconBase64}`
    : "";

  const renderedMessages = messages.map(renderMessage).join("\n");

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: #0d1117;
    font-family: 'JetBrains Mono', 'SF Mono', 'Fira Code', 'Cascadia Code', Menlo, monospace;
    font-size: 13px;
    line-height: 1.6;
    color: #c9d1d9;
    width: ${width}px;
  }

  /* ── Header ── */
  .header {
    padding: 14px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    border-bottom: 1px solid #21262d;
    background: #0d1117;
  }

  .header-icon {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
  }

  .header-title {
    font-size: 13px;
    font-weight: 600;
    color: #e6edf3;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .header-version {
    color: #6e7681;
    font-weight: 400;
    font-size: 12px;
  }

  .header-meta {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 16px;
    font-size: 11px;
    color: #6e7681;
  }

  .model-badge {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    color: #8b949e;
  }

  /* ── Session area ── */
  .session {
    padding: 4px 0;
  }

  /* ── User message ── */
  .msg-user {
    padding: 12px 20px;
    background: #161b22;
    border-bottom: 1px solid #21262d;
    border-top: 1px solid #21262d;
    margin: 4px 0;
  }

  .user-marker {
    color: #8b949e;
    font-weight: 700;
    margin-right: 8px;
    user-select: none;
  }

  .user-text {
    color: #e6edf3;
  }

  /* ── Assistant message (white circle) ── */
  .msg-assistant {
    padding: 12px 20px;
    display: flex;
    gap: 10px;
    align-items: flex-start;
  }

  .circle-white {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #e6edf3;
    flex-shrink: 0;
    margin-top: 6px;
  }

  .assistant-text {
    color: #c9d1d9;
    white-space: pre-wrap;
    word-wrap: break-word;
    flex: 1;
  }

  .assistant-text code {
    color: #58a6ff;
    font-size: 12.5px;
  }

  .assistant-text strong {
    color: #e6edf3;
    font-weight: 600;
  }

  /* ── Tool call (green circle) ── */
  .tool-block {
    padding: 6px 20px;
    display: flex;
    gap: 10px;
    align-items: flex-start;
  }

  .circle-green {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #3fb950;
    flex-shrink: 0;
    margin-top: 5px;
  }

  .tool-info {
    flex: 1;
  }

  .tool-header-line {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
  }

  .tool-name {
    color: #e6edf3;
    font-weight: 600;
  }

  .tool-header-detail {
    color: #8b949e;
    font-size: 12px;
  }

  .tool-collapse-hint {
    color: #6e7681;
    font-size: 11px;
    margin-left: auto;
  }

  .tool-content {
    margin-top: 6px;
    padding: 8px 12px;
    font-size: 12px;
    color: #8b949e;
    white-space: pre-wrap;
    word-wrap: break-word;
    background: #161b22;
    border-radius: 4px;
    border: 1px solid #21262d;
  }

  /* collapsed tool: just the header, no content */
  .tool-collapsed .tool-content {
    display: none;
  }

  .tool-collapsed .tool-collapse-hint::before {
    content: "▶";
    margin-right: 4px;
  }

  /* ── Diff in tool content ── */
  .diff-block {
    margin-top: 6px;
    font-size: 12px;
    background: #161b22;
    border-radius: 4px;
    border: 1px solid #21262d;
    overflow: hidden;
  }

  .diff-line {
    padding: 1px 12px;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: inherit;
  }

  .diff-removed {
    background: #3d1f1f;
    color: #f85149;
  }

  .diff-added {
    background: #1a3a1a;
    color: #3fb950;
  }

  .diff-context {
    color: #6e7681;
  }

  /* ── End of work ── */
  .msg-end {
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #6e7681;
    border-top: 1px solid #21262d;
    margin-top: 8px;
  }

  .end-icon {
    font-size: 14px;
    color: #6e7681;
  }

  .end-cost {
    margin-left: auto;
    color: #6e7681;
  }

  /* ── Input prompt at bottom ── */
  .input-area {
    padding: 12px 20px 16px;
    background: #161b22;
    border-top: 1px solid #21262d;
    margin-top: 4px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .input-marker {
    color: #8b949e;
    font-weight: 700;
    flex-shrink: 0;
  }

  .input-cursor {
    display: inline-block;
    width: 7px;
    height: 15px;
    background: #c9d1d9;
    opacity: 0.6;
    border-radius: 1px;
  }

  .cwd-label {
    font-size: 11px;
    color: #484f58;
    margin-left: auto;
  }
</style>
</head>
<body>
  <div class="header">
    ${iconSrc ? `<img class="header-icon" src="${iconSrc}" alt="">` : ""}
    <span class="header-title">
      Claude Code
      <span class="header-version">v2.0.8</span>
    </span>
    <div class="header-meta">
      ${project ? `<span>${escapeHtml(project)}</span>` : ""}
      <span class="model-badge">${escapeHtml(model)}</span>
    </div>
  </div>

  <div class="session">
${renderedMessages}
  </div>

  ${showInput ? `<div class="input-area">
    <span class="input-marker">&gt;</span>
    <span class="input-cursor"></span>
    <span class="cwd-label">${escapeHtml(cwd)}</span>
  </div>` : ""}
</body>
</html>`;
}

// ---------------------------------------------------------------------------
// Message renderers
// ---------------------------------------------------------------------------

function renderMessage(msg) {
  switch (msg.role) {
    case "user":
      return `    <div class="msg-user">
      <span class="user-marker">&gt;</span><span class="user-text">${escapeHtml(msg.text)}</span>
    </div>`;

    case "assistant":
      return `    <div class="msg-assistant">
      <span class="circle-white"></span>
      <span class="assistant-text">${formatAssistantText(msg.text)}</span>
    </div>`;

    case "tool_call":
      return renderToolCall(msg);

    case "end":
      return `    <div class="msg-end">
      <span class="end-icon">✻</span>
      <span>${escapeHtml(msg.text)}</span>
      ${msg.cost ? `<span class="end-cost">${escapeHtml(msg.cost)}</span>` : ""}
    </div>`;

    default:
      return "";
  }
}

function renderToolCall(msg) {
  const collapsed = msg.collapsed ? " tool-collapsed" : "";
  let contentHtml = "";

  if (msg.diff) {
    contentHtml = renderDiff(msg.diff);
  } else if (msg.content) {
    contentHtml = `      <div class="tool-content">${escapeHtml(msg.content)}</div>`;
  }

  return `    <div class="tool-block${collapsed}">
      <span class="circle-green"></span>
      <div class="tool-info">
        <div class="tool-header-line">
          <span class="tool-name">${escapeHtml(msg.tool)}</span>
          ${msg.header ? `<span class="tool-header-detail">${escapeHtml(msg.header)}</span>` : ""}
          ${msg.collapsed ? `<span class="tool-collapse-hint"></span>` : ""}
        </div>
${contentHtml}
      </div>
    </div>`;
}

function renderDiff(diff) {
  let lines = "";

  if (diff.removed) {
    for (const line of diff.removed) {
      lines += `<div class="diff-line diff-removed">- ${escapeHtml(line)}</div>`;
    }
  }
  if (diff.added) {
    for (const line of diff.added) {
      lines += `<div class="diff-line diff-added">+ ${escapeHtml(line)}</div>`;
    }
  }

  return `      <div class="diff-block">${lines}</div>`;
}

function formatAssistantText(text) {
  let escaped = escapeHtml(text);
  escaped = escaped.replace(/`([^`]+)`/g, "<code>$1</code>");
  escaped = escaped.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  return escaped;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
