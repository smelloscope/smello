/**
 * Anthropic Messages API adapter.
 *
 * Parses `POST /v1/messages` request bodies, non-streaming response bodies, and
 * streaming SSE responses into the shared {@link LlmView} model. Tolerant by
 * design: unrecognized content maps to `kind: "unknown"` rather than being dropped.
 */
import type { SseEvent } from "../components/SseViewer";
import type { LlmBlock, LlmMessage, LlmTool, LlmUsage, LlmView } from "./types";
import { asString, isRecord, numOrUndef, tryParseJson } from "./util";

function usageOf(u: unknown): LlmUsage | undefined {
  if (!isRecord(u)) return undefined;
  const usage: LlmUsage = {
    inputTokens: numOrUndef(u.input_tokens),
    outputTokens: numOrUndef(u.output_tokens),
    cacheReadTokens: numOrUndef(u.cache_read_input_tokens),
    cacheWriteTokens: numOrUndef(u.cache_creation_input_tokens),
  };
  return Object.values(usage).some((v) => v !== undefined) ? usage : undefined;
}

function blockOf(b: unknown): LlmBlock {
  if (!isRecord(b)) return { kind: "unknown", raw: b };
  switch (b.type) {
    case "text":
      return { kind: "text", text: asString(b.text) };
    case "thinking":
      return { kind: "thinking", text: asString(b.thinking) };
    case "redacted_thinking":
      return { kind: "thinking", text: "[redacted thinking]" };
    case "image":
      return {
        kind: "image",
        media: isRecord(b.source) ? asString(b.source.media_type) : undefined,
      };
    case "tool_use":
      return {
        kind: "tool_use",
        name: asString(b.name),
        id: asString(b.id) || undefined,
        input: b.input,
      };
    case "tool_result":
      return {
        kind: "tool_result",
        toolUseId: asString(b.tool_use_id) || undefined,
        content: b.content,
        isError: b.is_error === true,
      };
    default:
      return { kind: "unknown", raw: b };
  }
}

function contentToBlocks(content: unknown): LlmBlock[] {
  if (typeof content === "string") return content ? [{ kind: "text", text: content }] : [];
  if (Array.isArray(content)) return content.map(blockOf);
  if (content == null) return [];
  return [{ kind: "unknown", raw: content }];
}

function systemToBlocks(system: unknown): LlmBlock[] | undefined {
  if (typeof system === "string") return system ? [{ kind: "text", text: system }] : undefined;
  if (Array.isArray(system)) return system.map(blockOf);
  return undefined;
}

function toolsOf(tools: unknown): LlmTool[] | undefined {
  if (!Array.isArray(tools)) return undefined;
  const mapped = tools
    .filter(isRecord)
    .map((t) => ({ name: asString(t.name), description: asString(t.description) || undefined }))
    .filter((t) => t.name);
  return mapped.length ? mapped : undefined;
}

/** OpenAI-specific fields that must never appear in an Anthropic request. */
function looksLikeOpenAi(messages: unknown[]): boolean {
  return messages.some(
    (m) =>
      isRecord(m) &&
      (m.role === "system" ||
        m.role === "tool" ||
        m.role === "developer" ||
        "tool_calls" in m ||
        "tool_call_id" in m),
  );
}

export function detectRequest(json: unknown): LlmView | null {
  if (!isRecord(json)) return null;
  if ("choices" in json || json.type === "message") return null;
  if (!Array.isArray(json.messages)) return null;
  if (looksLikeOpenAi(json.messages)) return null;

  // Positive Anthropic signal — `max_tokens` is required by the API, `system` is
  // top-level (never a message role). Guards against claiming a bare OpenAI request.
  const hasSignal =
    "max_tokens" in json ||
    "system" in json ||
    json.messages.some((m) => isRecord(m) && Array.isArray(m.content));
  if (!hasSignal) return null;

  const messages: LlmMessage[] = json.messages.filter(isRecord).map((m) => ({
    role: m.role === "assistant" ? "assistant" : "user",
    blocks: contentToBlocks(m.content),
  }));

  return {
    provider: "anthropic",
    kind: "request",
    model: asString(json.model) || undefined,
    system: systemToBlocks(json.system),
    messages,
    tools: toolsOf(json.tools),
  };
}

export function detectResponse(json: unknown): LlmView | null {
  if (!isRecord(json)) return null;
  if (json.type !== "message" || json.role !== "assistant") return null;
  if (!Array.isArray(json.content)) return null;

  return {
    provider: "anthropic",
    kind: "response",
    model: asString(json.model) || undefined,
    messages: [{ role: "assistant", blocks: json.content.map(blockOf) }],
    stopReason: asString(json.stop_reason) || undefined,
    usage: usageOf(json.usage),
  };
}

// --- Streaming reassembly ---------------------------------------------------

type PendingBlock = { block: LlmBlock; jsonBuf?: string };

function seedBlock(cb: unknown): PendingBlock {
  if (!isRecord(cb)) return { block: { kind: "unknown", raw: cb } };
  switch (cb.type) {
    case "text":
      return { block: { kind: "text", text: asString(cb.text) } };
    case "thinking":
      return { block: { kind: "thinking", text: asString(cb.thinking) } };
    case "tool_use":
      return {
        block: {
          kind: "tool_use",
          name: asString(cb.name),
          id: asString(cb.id) || undefined,
          input: undefined,
        },
        jsonBuf: "",
      };
    default:
      return { block: { kind: "unknown", raw: cb } };
  }
}

function applyDelta(pending: PendingBlock | undefined, delta: unknown): void {
  if (!pending || !isRecord(delta)) return;
  const { block } = pending;
  if (delta.type === "text_delta" && block.kind === "text") {
    block.text += asString(delta.text);
  } else if (delta.type === "thinking_delta" && block.kind === "thinking") {
    block.text += asString(delta.thinking);
  } else if (delta.type === "input_json_delta" && pending.jsonBuf !== undefined) {
    pending.jsonBuf += asString(delta.partial_json);
  }
}

function finalize(pending: PendingBlock): LlmBlock {
  const { block, jsonBuf } = pending;
  if (block.kind === "tool_use" && jsonBuf !== undefined) {
    block.input = jsonBuf ? (tryParseJson(jsonBuf) ?? jsonBuf) : undefined;
  }
  return block;
}

export function detectStream(events: SseEvent[]): LlmView | null {
  const parsed = events.map((e) => ({
    name: e.event,
    data: e.data ? tryParseJson(e.data) : null,
  }));
  const typeOf = (p: (typeof parsed)[number]): string =>
    isRecord(p.data) && typeof p.data.type === "string" ? p.data.type : (p.name ?? "");

  if (!parsed.some((p) => typeOf(p) === "message_start")) return null;

  let model: string | undefined;
  let usage: LlmUsage | undefined;
  let stopReason: string | undefined;
  const pending: PendingBlock[] = [];

  for (const p of parsed) {
    const data = p.data;
    if (!isRecord(data)) continue;
    switch (typeOf(p)) {
      case "message_start":
        if (isRecord(data.message)) {
          model = asString(data.message.model) || undefined;
          usage = usageOf(data.message.usage);
        }
        break;
      case "content_block_start": {
        const idx = numOrUndef(data.index) ?? pending.length;
        pending[idx] = seedBlock(data.content_block);
        break;
      }
      case "content_block_delta": {
        const idx = numOrUndef(data.index) ?? pending.length - 1;
        applyDelta(pending[idx], data.delta);
        break;
      }
      case "message_delta":
        if (isRecord(data.delta)) stopReason = asString(data.delta.stop_reason) || stopReason;
        if (isRecord(data.usage)) {
          const out = numOrUndef(data.usage.output_tokens);
          if (out !== undefined) usage = { ...usage, outputTokens: out };
        }
        break;
    }
  }

  const blocks = pending.filter(Boolean).map(finalize);
  return {
    provider: "anthropic",
    kind: "response",
    model,
    messages: [{ role: "assistant", blocks }],
    stopReason,
    usage,
  };
}
