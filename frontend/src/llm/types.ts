/**
 * Shared, provider-agnostic model for a single LLM call.
 *
 * Per-provider adapters (`anthropic.ts`, `openai.ts`) parse raw request/response
 * bodies into these types; `LlmView.tsx` renders them without knowing the provider.
 * Adding a new provider means adding an adapter, not touching this model or the renderer.
 */

export type LlmProvider = "anthropic" | "openai";

export type LlmRole = "system" | "user" | "assistant" | "tool";

/** A single piece of message content. `unknown` is a fallback so no data is ever dropped. */
export type LlmBlock =
  | { kind: "text"; text: string }
  | { kind: "thinking"; text: string }
  | { kind: "tool_use"; name: string; id?: string; input: unknown }
  | { kind: "tool_result"; toolUseId?: string; content: unknown; isError?: boolean }
  | { kind: "image"; media?: string }
  | { kind: "unknown"; raw: unknown };

export type LlmMessage = {
  role: LlmRole;
  blocks: LlmBlock[];
};

export type LlmUsage = {
  inputTokens?: number;
  outputTokens?: number;
  cacheReadTokens?: number;
  cacheWriteTokens?: number;
};

export type LlmTool = {
  name: string;
  description?: string;
};

export type LlmView = {
  provider: LlmProvider;
  kind: "request" | "response";
  model?: string;
  /** Top-level system prompt (Anthropic `system`, or an OpenAI `system`/`developer` message). */
  system?: LlmBlock[];
  messages: LlmMessage[];
  /** Tools declared on a request. */
  tools?: LlmTool[];
  /** Response only. */
  stopReason?: string;
  /** Response only. */
  usage?: LlmUsage;
};
