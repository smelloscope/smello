import { describe, it, expect } from "vitest";
import type { SseEvent } from "../components/SseViewer";
import { detectRequest, detectResponse, detectStream } from "./openai";

function sse(data: unknown): SseEvent {
  return { data: JSON.stringify(data), comments: [] };
}

describe("openai.detectRequest", () => {
  it("parses messages, extracting system and tool role", () => {
    const view = detectRequest({
      model: "gpt-4o",
      tools: [{ type: "function", function: { name: "get_weather", description: "weather" } }],
      messages: [
        { role: "system", content: "Be terse." },
        { role: "user", content: "weather?" },
        {
          role: "assistant",
          content: null,
          tool_calls: [
            {
              id: "call_1",
              type: "function",
              function: { name: "get_weather", arguments: '{"city":"SF"}' },
            },
          ],
        },
        { role: "tool", tool_call_id: "call_1", content: "sunny" },
      ],
    });
    expect(view).not.toBeNull();
    expect(view!.provider).toBe("openai");
    expect(view!.system).toEqual([{ kind: "text", text: "Be terse." }]);
    expect(view!.tools).toEqual([{ name: "get_weather", description: "weather" }]);
    expect(view!.messages[0]!).toEqual({
      role: "user",
      blocks: [{ kind: "text", text: "weather?" }],
    });
    expect(view!.messages[1]!.blocks[0]).toEqual({
      kind: "tool_use",
      name: "get_weather",
      id: "call_1",
      input: { city: "SF" },
    });
    expect(view!.messages[2]!).toEqual({
      role: "tool",
      blocks: [{ kind: "tool_result", toolUseId: "call_1", content: "sunny" }],
    });
  });

  it("requires an OpenAI signal — a bare messages array is not claimed", () => {
    // A non-LLM payload that merely has a `messages` array must fall through.
    expect(detectRequest({ messages: [{ id: 1, text: "hello" }] })).toBeNull();
    expect(detectRequest({ messages: [] })).toBeNull();
  });

  it("accepts a chat request signalled by role-shaped messages (no model)", () => {
    const view = detectRequest({ messages: [{ role: "user", content: "hi" }] });
    expect(view).not.toBeNull();
    expect(view!.provider).toBe("openai");
    expect(view!.messages[0]).toEqual({ role: "user", blocks: [{ kind: "text", text: "hi" }] });
  });
});

describe("openai.detectResponse", () => {
  it("parses choices[0].message with tool_calls and usage", () => {
    const view = detectResponse({
      object: "chat.completion",
      model: "gpt-4o",
      choices: [
        {
          index: 0,
          message: {
            role: "assistant",
            content: "Here you go",
            tool_calls: [
              { id: "call_9", type: "function", function: { name: "f", arguments: "{}" } },
            ],
          },
          finish_reason: "tool_calls",
        },
      ],
      usage: { prompt_tokens: 20, completion_tokens: 8, total_tokens: 28 },
    });
    expect(view).not.toBeNull();
    expect(view!.kind).toBe("response");
    expect(view!.stopReason).toBe("tool_calls");
    expect(view!.usage).toEqual({ inputTokens: 20, outputTokens: 8 });
    expect(view!.messages[0]!.blocks).toEqual([
      { kind: "text", text: "Here you go" },
      { kind: "tool_use", name: "f", id: "call_9", input: {} },
    ]);
  });

  it("returns null when there are no choices", () => {
    expect(detectResponse({ type: "message", role: "assistant", content: [] })).toBeNull();
  });

  it("maps the OpenRouter/DeepSeek `reasoning` field to a thinking block", () => {
    const view = detectResponse({
      object: "chat.completion",
      model: "deepseek/deepseek-v4-flash",
      choices: [
        {
          index: 0,
          message: {
            role: "assistant",
            content: null,
            reasoning: "The user wants the weather. Let me call the tool.",
            tool_calls: [
              {
                id: "call_1",
                type: "function",
                function: { name: "get_weather", arguments: '{"city":"Paris"}' },
              },
            ],
          },
          finish_reason: "tool_calls",
        },
      ],
    });
    expect(view!.messages[0]!.blocks).toEqual([
      { kind: "thinking", text: "The user wants the weather. Let me call the tool." },
      { kind: "tool_use", name: "get_weather", id: "call_1", input: { city: "Paris" } },
    ]);
  });
});

describe("openai.detectStream", () => {
  it("reassembles streamed content and tool call arguments", () => {
    const events: SseEvent[] = [
      sse({
        object: "chat.completion.chunk",
        model: "gpt-4o",
        choices: [{ index: 0, delta: { role: "assistant", content: "Hel" } }],
      }),
      sse({ object: "chat.completion.chunk", choices: [{ index: 0, delta: { content: "lo" } }] }),
      sse({
        object: "chat.completion.chunk",
        choices: [
          {
            index: 0,
            delta: {
              tool_calls: [{ index: 0, id: "call_1", function: { name: "f", arguments: '{"a":' } }],
            },
          },
        ],
      }),
      sse({
        object: "chat.completion.chunk",
        choices: [
          { index: 0, delta: { tool_calls: [{ index: 0, function: { arguments: "1}" } }] } },
        ],
      }),
      sse({
        object: "chat.completion.chunk",
        choices: [{ index: 0, delta: {}, finish_reason: "tool_calls" }],
      }),
      sse({
        object: "chat.completion.chunk",
        choices: [],
        usage: { prompt_tokens: 5, completion_tokens: 3 },
      }),
    ];
    const view = detectStream(events);
    expect(view).not.toBeNull();
    expect(view!.model).toBe("gpt-4o");
    expect(view!.stopReason).toBe("tool_calls");
    expect(view!.usage).toEqual({ inputTokens: 5, outputTokens: 3 });
    expect(view!.messages[0]!.blocks).toEqual([
      { kind: "text", text: "Hello" },
      { kind: "tool_use", name: "f", id: "call_1", input: { a: 1 } },
    ]);
  });

  it("returns null for a non-OpenAI stream", () => {
    expect(detectStream([sse({ type: "message_start" })])).toBeNull();
  });
});

describe("openai Responses API (/v1/responses)", () => {
  it("parses a request with instructions, mixed input items, and tools", () => {
    const view = detectRequest({
      model: "gpt-4o-mini",
      instructions: "You are a concise weather assistant.",
      tools: [{ name: "get_weather", parameters: { type: "object" } }],
      input: [
        { role: "user", content: "What's the weather in Paris?" },
        {
          type: "function_call",
          call_id: "call_1",
          name: "get_weather",
          arguments: '{"city":"Paris"}',
        },
        { type: "function_call_output", call_id: "call_1", output: "18°C and sunny" },
      ],
    });
    expect(view).not.toBeNull();
    expect(view!.provider).toBe("openai");
    expect(view!.kind).toBe("request");
    expect(view!.system).toEqual([{ kind: "text", text: "You are a concise weather assistant." }]);
    expect(view!.tools).toEqual([{ name: "get_weather", description: undefined }]);
    expect(view!.messages[0]).toEqual({
      role: "user",
      blocks: [{ kind: "text", text: "What's the weather in Paris?" }],
    });
    expect(view!.messages[1]).toEqual({
      role: "assistant",
      blocks: [{ kind: "tool_use", name: "get_weather", id: "call_1", input: { city: "Paris" } }],
    });
    expect(view!.messages[2]).toEqual({
      role: "tool",
      blocks: [{ kind: "tool_result", toolUseId: "call_1", content: "18°C and sunny" }],
    });
  });

  it("parses a response with output_text and usage", () => {
    const view = detectResponse({
      object: "response",
      model: "gpt-4o-mini",
      status: "completed",
      output: [
        {
          type: "message",
          role: "assistant",
          content: [{ type: "output_text", text: "The weather in Paris is 18°C and sunny." }],
        },
      ],
      usage: { input_tokens: 105, output_tokens: 13, input_tokens_details: { cached_tokens: 4 } },
    });
    expect(view).not.toBeNull();
    expect(view!.kind).toBe("response");
    expect(view!.stopReason).toBe("completed");
    expect(view!.usage).toEqual({ inputTokens: 105, outputTokens: 13, cacheReadTokens: 4 });
    expect(view!.messages[0]).toEqual({
      role: "assistant",
      blocks: [{ kind: "text", text: "The weather in Paris is 18°C and sunny." }],
    });
  });

  it("requires a Responses signal — ordinary input/output bodies are not claimed", () => {
    // `input` / `output` are common field names; without Responses-specific structure
    // these must fall through to the normal JSON tree, not the LLM view.
    expect(detectRequest({ input: "just some text" })).toBeNull();
    expect(detectRequest({ input: [{ foo: 1 }, { bar: 2 }] })).toBeNull();
    // An ML inference API body has the same `{ model, input }` shape — must not match.
    expect(detectRequest({ model: "resnet-50", input: "cat.jpg" })).toBeNull();
    expect(detectRequest({ model: "embed-v1", input: { image_url: "..." } })).toBeNull();
    expect(detectRequest({ model: "m", input: [{ type: "row", value: 1 }] })).toBeNull();
    // `type: "message"` and bare `role`+`content` are common in non-LLM JSON — the
    // signal must be a function-call item or top-level `instructions`, not these.
    expect(detectRequest({ model: "m", input: [{ type: "message", text: "hi" }] })).toBeNull();
    expect(detectRequest({ input: [{ role: "admin", content: "grant" }] })).toBeNull();
    expect(detectResponse({ output: [1, 2, 3] })).toBeNull();
    expect(detectResponse({ output: [{ note: "hello" }] })).toBeNull();
  });

  it("accepts a Responses request signalled by function-call items (no instructions)", () => {
    const view = detectRequest({
      model: "gpt-4o",
      input: [
        { role: "user", content: "weather?" },
        {
          type: "function_call",
          call_id: "c1",
          name: "get_weather",
          arguments: '{"city":"Paris"}',
        },
      ],
    });
    expect(view).not.toBeNull();
    expect(view!.messages[1]).toEqual({
      role: "assistant",
      blocks: [{ kind: "tool_use", name: "get_weather", id: "c1", input: { city: "Paris" } }],
    });
  });

  it("accepts a message-only request signalled by instructions + a turn list", () => {
    // The first call of an agent turn: instructions + a single user message, no tools yet.
    const view = detectRequest({
      model: "gpt-4o",
      instructions: "You are a concise weather assistant.",
      input: [{ role: "user", content: "What's the weather in Paris?" }],
    });
    expect(view).not.toBeNull();
    expect(view!.system).toEqual([{ kind: "text", text: "You are a concise weather assistant." }]);
    expect(view!.messages[0]).toEqual({
      role: "user",
      blocks: [{ kind: "text", text: "What's the weather in Paris?" }],
    });
  });

  it("does not claim string-input bodies (too ambiguous with templating APIs)", () => {
    // `{ input, instructions }` as two strings is not distinctive enough — fall through.
    expect(detectRequest({ model: "gpt-4o", input: "hi", instructions: "Be nice." })).toBeNull();
    expect(detectRequest({ model: "gpt-4o", input: "hi" })).toBeNull();
    // instructions + a non-conversation array is likewise not claimed.
    expect(detectRequest({ instructions: "x", input: [{ type: "row", value: 1 }] })).toBeNull();
  });

  it("requires a call_id on function-call items — the type alone is not a signal", () => {
    // A `{ type: "function_call" }` without a call_id is not distinctively OpenAI.
    expect(
      detectRequest({ model: "m", input: [{ type: "function_call", name: "x", arguments: "{}" }] }),
    ).toBeNull();
    // …even paired with instructions, since it isn't a valid conversation turn.
    expect(
      detectRequest({ instructions: "go", input: [{ type: "function_call", name: "x" }] }),
    ).toBeNull();
  });

  it("parses a response whose output is a function_call", () => {
    const view = detectResponse({
      object: "response",
      model: "gpt-4o-mini",
      status: "completed",
      output: [
        {
          type: "function_call",
          call_id: "call_9",
          name: "get_weather",
          arguments: '{"city":"Paris"}',
        },
      ],
      usage: { input_tokens: 71, output_tokens: 15 },
    });
    expect(view!.messages[0]).toEqual({
      role: "assistant",
      blocks: [{ kind: "tool_use", name: "get_weather", id: "call_9", input: { city: "Paris" } }],
    });
  });
});
