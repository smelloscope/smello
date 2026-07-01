import { describe, it, expect } from "vitest";
import type { SseEvent } from "../components/SseViewer";
import { detectRequest, detectResponse, detectStream } from "./anthropic";

function sse(event: string, data: unknown): SseEvent {
  return { event, data: JSON.stringify(data), comments: [] };
}

describe("anthropic.detectRequest", () => {
  it("parses a request with string content and system + tools", () => {
    const view = detectRequest({
      model: "claude-opus-4-8",
      max_tokens: 1024,
      system: "You are helpful.",
      tools: [{ name: "get_weather", description: "Look up weather", input_schema: {} }],
      messages: [{ role: "user", content: "Hello" }],
    });
    expect(view).not.toBeNull();
    expect(view!.provider).toBe("anthropic");
    expect(view!.kind).toBe("request");
    expect(view!.model).toBe("claude-opus-4-8");
    expect(view!.system).toEqual([{ kind: "text", text: "You are helpful." }]);
    expect(view!.tools).toEqual([{ name: "get_weather", description: "Look up weather" }]);
    expect(view!.messages).toEqual([{ role: "user", blocks: [{ kind: "text", text: "Hello" }] }]);
  });

  it("parses block content including tool_use and tool_result", () => {
    const view = detectRequest({
      model: "claude-opus-4-8",
      max_tokens: 100,
      messages: [
        { role: "user", content: [{ type: "text", text: "weather?" }] },
        {
          role: "assistant",
          content: [{ type: "tool_use", id: "tu_1", name: "get_weather", input: { city: "SF" } }],
        },
        {
          role: "user",
          content: [
            { type: "tool_result", tool_use_id: "tu_1", content: "sunny", is_error: false },
          ],
        },
      ],
    });
    expect(view).not.toBeNull();
    expect(view!.messages[1]!.blocks[0]).toEqual({
      kind: "tool_use",
      name: "get_weather",
      id: "tu_1",
      input: { city: "SF" },
    });
    expect(view!.messages[2]!.blocks[0]).toEqual({
      kind: "tool_result",
      toolUseId: "tu_1",
      content: "sunny",
      isError: false,
    });
  });

  it("rejects an OpenAI-shaped request (system role message)", () => {
    expect(
      detectRequest({
        model: "gpt-4o",
        messages: [
          { role: "system", content: "hi" },
          { role: "user", content: "hey" },
        ],
      }),
    ).toBeNull();
  });
});

describe("anthropic.detectResponse", () => {
  it("parses a non-streaming assistant message with usage", () => {
    const view = detectResponse({
      id: "msg_1",
      type: "message",
      role: "assistant",
      model: "claude-opus-4-8",
      content: [{ type: "text", text: "Hi there" }],
      stop_reason: "end_turn",
      usage: { input_tokens: 10, output_tokens: 5, cache_read_input_tokens: 2 },
    });
    expect(view).not.toBeNull();
    expect(view!.kind).toBe("response");
    expect(view!.stopReason).toBe("end_turn");
    expect(view!.usage).toEqual({
      inputTokens: 10,
      outputTokens: 5,
      cacheReadTokens: 2,
      cacheWriteTokens: undefined,
    });
    expect(view!.messages[0]!.blocks[0]).toEqual({ kind: "text", text: "Hi there" });
  });

  it("returns null for a non-message body", () => {
    expect(detectResponse({ type: "error", error: {} })).toBeNull();
    expect(detectResponse({ choices: [] })).toBeNull();
  });
});

describe("anthropic.detectStream", () => {
  it("reassembles text and a tool_use block from SSE events", () => {
    const events: SseEvent[] = [
      sse("message_start", {
        type: "message_start",
        message: { model: "claude-opus-4-8", usage: { input_tokens: 12, output_tokens: 1 } },
      }),
      sse("content_block_start", {
        type: "content_block_start",
        index: 0,
        content_block: { type: "text", text: "" },
      }),
      sse("content_block_delta", {
        type: "content_block_delta",
        index: 0,
        delta: { type: "text_delta", text: "Let me " },
      }),
      sse("content_block_delta", {
        type: "content_block_delta",
        index: 0,
        delta: { type: "text_delta", text: "check." },
      }),
      sse("content_block_stop", { type: "content_block_stop", index: 0 }),
      sse("content_block_start", {
        type: "content_block_start",
        index: 1,
        content_block: { type: "tool_use", id: "tu_9", name: "get_weather", input: {} },
      }),
      sse("content_block_delta", {
        type: "content_block_delta",
        index: 1,
        delta: { type: "input_json_delta", partial_json: '{"city":' },
      }),
      sse("content_block_delta", {
        type: "content_block_delta",
        index: 1,
        delta: { type: "input_json_delta", partial_json: '"SF"}' },
      }),
      sse("content_block_stop", { type: "content_block_stop", index: 1 }),
      sse("message_delta", {
        type: "message_delta",
        delta: { stop_reason: "tool_use" },
        usage: { output_tokens: 25 },
      }),
      sse("message_stop", { type: "message_stop" }),
    ];
    const view = detectStream(events);
    expect(view).not.toBeNull();
    expect(view!.model).toBe("claude-opus-4-8");
    expect(view!.stopReason).toBe("tool_use");
    expect(view!.usage).toEqual({
      inputTokens: 12,
      outputTokens: 25,
      cacheReadTokens: undefined,
      cacheWriteTokens: undefined,
    });
    expect(view!.messages[0]!.blocks).toEqual([
      { kind: "text", text: "Let me check." },
      { kind: "tool_use", name: "get_weather", id: "tu_9", input: { city: "SF" } },
    ]);
  });

  it("returns null for a non-Anthropic SSE stream", () => {
    expect(detectStream([sse("foo", { type: "bar" })])).toBeNull();
  });
});
