/**
 * Provider registry. Tries each adapter in order and returns the first match.
 *
 * These are the only entry points `BodyViewer` calls — it never imports a
 * specific provider. Adding a provider means adding its adapter to a list here.
 */
import type { SseEvent } from "../components/SseViewer";
import type { LlmView } from "./types";
import * as anthropic from "./anthropic";
import * as openai from "./openai";

// Order matters for requests: Anthropic is precise and runs first; OpenAI is the
// broader fallback for any `messages`-shaped body Anthropic declines.
const adapters = [anthropic, openai];

/** Detect an LLM request from a parsed JSON body. */
export function detectLlmRequest(json: unknown): LlmView | null {
  for (const a of adapters) {
    const view = a.detectRequest(json);
    if (view) return view;
  }
  return null;
}

/** Detect a non-streaming LLM response from a parsed JSON body. */
export function detectLlmResponse(json: unknown): LlmView | null {
  for (const a of adapters) {
    const view = a.detectResponse(json);
    if (view) return view;
  }
  return null;
}

/** Detect and reassemble a streaming LLM response from parsed SSE events. */
export function detectLlmStreamResponse(events: SseEvent[]): LlmView | null {
  for (const a of adapters) {
    const view = a.detectStream(events);
    if (view) return view;
  }
  return null;
}
