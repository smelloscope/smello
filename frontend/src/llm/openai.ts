/**
 * OpenAI adapter — handles both OpenAI HTTP APIs behind one provider:
 *   - Chat Completions (`POST /v1/chat/completions`): `messages[]`, tool calls in a
 *     separate `tool_calls` field, tool results as `role: "tool"` messages.
 *   - Responses (`POST /v1/responses`, used by the OpenAI Agents SDK): `instructions`
 *     + a flat `input[]`/`output[]` array mixing `message`, `function_call`, and
 *     `function_call_output` items with `output_text` content parts.
 * Both normalize into the shared {@link LlmView} model so the renderer stays uniform.
 */
import type { SseEvent } from "../components/SseViewer";
import type { LlmBlock, LlmMessage, LlmRole, LlmTool, LlmUsage, LlmView } from "./types";
import { asString, isRecord, numOrUndef, tryParseJson } from "./util";

function usageOf(u: unknown): LlmUsage | undefined {
  if (!isRecord(u)) return undefined;
  const usage: LlmUsage = {
    inputTokens: numOrUndef(u.prompt_tokens),
    outputTokens: numOrUndef(u.completion_tokens),
  };
  return Object.values(usage).some((v) => v !== undefined) ? usage : undefined;
}

/** Tool-call arguments are a JSON string; parse when possible, else keep raw. */
function parseArgs(args: unknown): unknown {
  const s = asString(args);
  return s ? (tryParseJson(s) ?? s) : {};
}

function contentToBlocks(content: unknown): LlmBlock[] {
  if (typeof content === "string") return content ? [{ kind: "text", text: content }] : [];
  if (Array.isArray(content)) {
    return content.map((p): LlmBlock => {
      if (!isRecord(p)) return { kind: "unknown", raw: p };
      if (p.type === "text" || p.type === "input_text" || p.type === "output_text") {
        return { kind: "text", text: asString(p.text) };
      }
      if (p.type === "image_url" || p.type === "input_image") return { kind: "image" };
      return { kind: "unknown", raw: p };
    });
  }
  return [];
}

function toolCallsToBlocks(toolCalls: unknown): LlmBlock[] {
  if (!Array.isArray(toolCalls)) return [];
  return toolCalls.filter(isRecord).map((tc): LlmBlock => {
    const fn = isRecord(tc.function) ? tc.function : {};
    return {
      kind: "tool_use",
      name: asString(fn.name),
      id: asString(tc.id) || undefined,
      input: parseArgs(fn.arguments),
    };
  });
}

function messageBlocks(m: Record<string, unknown>): LlmBlock[] {
  if (m.role === "tool") {
    return [
      { kind: "tool_result", toolUseId: asString(m.tool_call_id) || undefined, content: m.content },
    ];
  }
  const blocks: LlmBlock[] = [];
  // `reasoning` is an OpenRouter/DeepSeek extension carrying the model's thinking.
  if (typeof m.reasoning === "string" && m.reasoning)
    blocks.push({ kind: "thinking", text: m.reasoning });
  blocks.push(...contentToBlocks(m.content), ...toolCallsToBlocks(m.tool_calls));
  return blocks;
}

function toolsOf(tools: unknown): LlmTool[] | undefined {
  if (!Array.isArray(tools)) return undefined;
  const mapped = tools
    .filter(isRecord)
    .map((t) => (isRecord(t.function) ? t.function : t))
    .map((f) => ({ name: asString(f.name), description: asString(f.description) || undefined }))
    .filter((t) => t.name);
  return mapped.length ? mapped : undefined;
}

function normalizeRole(role: unknown): LlmRole {
  if (role === "assistant") return "assistant";
  if (role === "tool") return "tool";
  return "user";
}

function detectChatRequest(json: unknown): LlmView | null {
  if (!isRecord(json)) return null;
  if ("choices" in json || json.type === "message") return null;
  if (!Array.isArray(json.messages)) return null;

  // Require an OpenAI-specific signal so an unrelated `{ messages: [...] }` payload
  // isn't coerced into the LLM view: a `model` field, chat-shaped role messages, or
  // tool-call fields. Without this, any body with a `messages` array would match.
  const msgs = json.messages;
  const hasSignal =
    "model" in json ||
    (msgs.length > 0 && msgs.every((m) => isRecord(m) && typeof m.role === "string")) ||
    msgs.some((m) => isRecord(m) && ("tool_calls" in m || "tool_call_id" in m));
  if (!hasSignal) return null;

  const system: LlmBlock[] = [];
  const messages: LlmMessage[] = [];
  for (const m of json.messages) {
    if (!isRecord(m)) continue;
    if (m.role === "system" || m.role === "developer") {
      system.push(...contentToBlocks(m.content));
    } else {
      messages.push({ role: normalizeRole(m.role), blocks: messageBlocks(m) });
    }
  }

  return {
    provider: "openai",
    kind: "request",
    model: asString(json.model) || undefined,
    system: system.length ? system : undefined,
    messages,
    tools: toolsOf(json.tools),
  };
}

function detectChatResponse(json: unknown): LlmView | null {
  if (!isRecord(json)) return null;
  if (!Array.isArray(json.choices) || json.choices.length === 0) return null;

  const choice = json.choices[0];
  if (!isRecord(choice)) return null;
  const message = isRecord(choice.message) ? choice.message : {};

  return {
    provider: "openai",
    kind: "response",
    model: asString(json.model) || undefined,
    messages: [{ role: "assistant", blocks: messageBlocks({ role: "assistant", ...message }) }],
    stopReason: asString(choice.finish_reason) || undefined,
    usage: usageOf(json.usage),
  };
}

// --- Responses API (/v1/responses) ------------------------------------------

function responsesUsage(u: unknown): LlmUsage | undefined {
  if (!isRecord(u)) return undefined;
  const details = isRecord(u.input_tokens_details) ? u.input_tokens_details : {};
  const usage: LlmUsage = {
    inputTokens: numOrUndef(u.input_tokens),
    outputTokens: numOrUndef(u.output_tokens),
    cacheReadTokens: numOrUndef(details.cached_tokens),
  };
  return Object.values(usage).some((v) => v !== undefined) ? usage : undefined;
}

function reasoningText(item: Record<string, unknown>): string {
  const parts: string[] = [];
  for (const key of ["summary", "content"]) {
    const arr = item[key];
    if (Array.isArray(arr)) {
      for (const p of arr) if (isRecord(p) && typeof p.text === "string") parts.push(p.text);
    }
  }
  return parts.join("\n");
}

/** Map one flat Responses `input`/`output` item into a role-tagged message. */
function responsesItem(item: unknown): LlmMessage {
  if (!isRecord(item)) return { role: "user", blocks: [{ kind: "unknown", raw: item }] };
  switch (item.type) {
    case "function_call":
      return {
        role: "assistant",
        blocks: [
          {
            kind: "tool_use",
            name: asString(item.name),
            id: asString(item.call_id) || asString(item.id) || undefined,
            input: parseArgs(item.arguments),
          },
        ],
      };
    case "function_call_output":
      return {
        role: "tool",
        blocks: [
          {
            kind: "tool_result",
            toolUseId: asString(item.call_id) || undefined,
            content: item.output,
          },
        ],
      };
    case "reasoning": {
      const text = reasoningText(item);
      return {
        role: "assistant",
        blocks: text ? [{ kind: "thinking", text }] : [{ kind: "unknown", raw: item }],
      };
    }
    default:
      // "message" item (or a bare {role, content} entry)
      return { role: normalizeRole(item.role), blocks: contentToBlocks(item.content) };
  }
}

/**
 * A `function_call`/`function_call_output` item. The `call_id` string is the unique
 * marker — a bare `{ type: "function_call" }` without one is not distinctively OpenAI.
 */
function isResponsesFunctionItem(it: unknown): boolean {
  return (
    isRecord(it) &&
    (it.type === "function_call" || it.type === "function_call_output") &&
    typeof it.call_id === "string"
  );
}

/** A conversation turn: a role-tagged message, a reasoning item, or a function-call item. */
function isResponsesConversationItem(it: unknown): boolean {
  if (!isRecord(it)) return false;
  return typeof it.role === "string" || it.type === "reasoning" || isResponsesFunctionItem(it);
}

function detectResponsesRequest(json: unknown): LlmView | null {
  if (!isRecord(json)) return null;
  if (!("input" in json) || "messages" in json || "choices" in json) return null;

  const input = json.input;
  const inputItems = Array.isArray(input) ? input : [];
  // `{ model, input }` is also the shape of ML inference APIs, and `type: "message"` /
  // `role`+`content` items appear in plenty of non-LLM JSON. Only claim the body on an
  // unambiguous Responses signal:
  //   1. a function-call item (carries a `call_id`), or
  //   2. top-level `instructions` AND an input array that is entirely conversation turns
  //      — `instructions` + a turn list is unambiguously an LLM request.
  // Otherwise fall through so ordinary bodies render as a normal JSON tree.
  const hasFunctionItem = inputItems.some(isResponsesFunctionItem);
  const isConversation = inputItems.length > 0 && inputItems.every(isResponsesConversationItem);
  if (!hasFunctionItem && !("instructions" in json && isConversation)) return null;

  const messages: LlmMessage[] = inputItems.map(responsesItem);

  const instructions = asString(json.instructions);
  return {
    provider: "openai",
    kind: "request",
    model: asString(json.model) || undefined,
    system: instructions ? [{ kind: "text", text: instructions }] : undefined,
    messages,
    tools: toolsOf(json.tools),
  };
}

function detectResponsesResponse(json: unknown): LlmView | null {
  if (!isRecord(json)) return null;
  if (!Array.isArray(json.output) || "choices" in json) return null;

  // `output` is a common field name, so require an unambiguous Responses signal: the
  // `object: "response"` marker, or an `output` array that is entirely Responses items
  // (message / function_call / reasoning) alongside `usage`. A plain `{ output: [...] }`
  // — even with `model`/`usage` — otherwise falls through to the normal JSON tree.
  const output = json.output;
  const looksLikeResponses =
    json.object === "response" ||
    ("usage" in json && output.length > 0 && output.every(isResponsesConversationItem));
  if (!looksLikeResponses) return null;

  return {
    provider: "openai",
    kind: "response",
    model: asString(json.model) || undefined,
    messages: json.output.map(responsesItem),
    stopReason: asString(json.status) || undefined,
    usage: responsesUsage(json.usage),
  };
}

export function detectRequest(json: unknown): LlmView | null {
  return detectChatRequest(json) ?? detectResponsesRequest(json);
}

export function detectResponse(json: unknown): LlmView | null {
  return detectChatResponse(json) ?? detectResponsesResponse(json);
}

// --- Streaming reassembly ---------------------------------------------------

type PendingToolCall = { id?: string; name: string; args: string };

export function detectStream(events: SseEvent[]): LlmView | null {
  const parsed = events.map((e) => (e.data ? tryParseJson(e.data) : null)).filter(isRecord);

  const isChunk = (d: Record<string, unknown>): boolean =>
    d.object === "chat.completion.chunk" ||
    (Array.isArray(d.choices) && d.choices.some((c) => isRecord(c) && "delta" in c));
  if (!parsed.some(isChunk)) return null;

  let model: string | undefined;
  let stopReason: string | undefined;
  let usage: LlmUsage | undefined;
  let text = "";
  let reasoning = "";
  const toolCalls: PendingToolCall[] = [];

  for (const d of parsed) {
    if (!model) model = asString(d.model) || undefined;
    const merged = usageOf(d.usage);
    if (merged) usage = merged;
    if (!Array.isArray(d.choices)) continue;
    const choice = d.choices[0];
    if (!isRecord(choice)) continue;
    if (choice.finish_reason) stopReason = asString(choice.finish_reason) || stopReason;
    const delta = isRecord(choice.delta) ? choice.delta : {};
    if (typeof delta.content === "string") text += delta.content;
    if (typeof delta.reasoning === "string") reasoning += delta.reasoning;
    if (Array.isArray(delta.tool_calls)) {
      for (const tc of delta.tool_calls) {
        if (!isRecord(tc)) continue;
        const idx = numOrUndef(tc.index) ?? toolCalls.length;
        const slot = (toolCalls[idx] ??= { name: "", args: "" });
        if (tc.id) slot.id = asString(tc.id);
        const fn = isRecord(tc.function) ? tc.function : {};
        if (fn.name) slot.name = asString(fn.name);
        if (fn.arguments) slot.args += asString(fn.arguments);
      }
    }
  }

  const blocks: LlmBlock[] = [];
  if (reasoning) blocks.push({ kind: "thinking", text: reasoning });
  if (text) blocks.push({ kind: "text", text });
  for (const tc of toolCalls.filter(Boolean)) {
    blocks.push({
      kind: "tool_use",
      name: tc.name,
      id: tc.id,
      input: tc.args ? (tryParseJson(tc.args) ?? tc.args) : {},
    });
  }

  return {
    provider: "openai",
    kind: "response",
    model,
    messages: [{ role: "assistant", blocks }],
    stopReason,
    usage,
  };
}
