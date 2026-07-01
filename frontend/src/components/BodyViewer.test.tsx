import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import BodyViewer from "./BodyViewer";

describe("BodyViewer", () => {
  it("renders nothing when data is null", () => {
    const { container } = render(<BodyViewer data={null} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders raw text for plain text (no tabs)", () => {
    render(<BodyViewer data="not valid json or xml" />);
    expect(screen.getByText("not valid json or xml")).toBeInTheDocument();
    expect(screen.getByText("not valid json or xml").tagName).toBe("PRE");
    expect(screen.queryByRole("tab")).not.toBeInTheDocument();
  });

  it("renders JSON with Tree/Raw tabs", () => {
    const { container } = render(<BodyViewer data='{"key":"value"}' />);
    const view = within(container);
    expect(view.getByRole("tab", { name: "Tree" })).toBeInTheDocument();
    expect(view.getByRole("tab", { name: "Raw" })).toBeInTheDocument();
    // Tree tab is default — json-view renders the parsed object
    expect(container.textContent).toContain("key");
    expect(container.textContent).toContain("value");
  });

  it("switches to Raw tab for JSON", async () => {
    const { container } = render(<BodyViewer data='{"key":"value"}' />);
    const view = within(container);
    await userEvent.click(view.getByRole("tab", { name: "Raw" }));
    // Raw tab shows syntax-highlighted JSON in a <pre>
    expect(container.querySelector("pre")!.textContent).toContain('"key"');
  });

  it("renders XML with Tree/Raw tabs", () => {
    const { container } = render(<BodyViewer data="<root><name>hello</name></root>" />);
    const view = within(container);
    expect(view.getByRole("tab", { name: "Tree" })).toBeInTheDocument();
    expect(view.getByRole("tab", { name: "Raw" })).toBeInTheDocument();
    // Tree tab shows parsed XML as JSON tree
    expect(container.textContent).toContain("name");
    expect(container.textContent).toContain("hello");
  });

  it("switches to Raw tab for XML", async () => {
    const { container } = render(<BodyViewer data="<root><name>hello</name></root>" />);
    const view = within(container);
    await userEvent.click(view.getByRole("tab", { name: "Raw" }));
    expect(container.querySelector("pre")!.textContent).toContain("<root>");
  });

  it("renders an LLM tab (default) for an Anthropic response body", () => {
    const body = JSON.stringify({
      type: "message",
      role: "assistant",
      model: "claude-opus-4-8",
      content: [{ type: "text", text: "Hello from Claude" }],
      stop_reason: "end_turn",
      usage: { input_tokens: 3, output_tokens: 2 },
    });
    const { container } = render(<BodyViewer data={body} />);
    const view = within(container);
    expect(view.getByRole("tab", { name: "LLM" })).toBeInTheDocument();
    expect(view.getByRole("tab", { name: "Tree" })).toBeInTheDocument();
    expect(view.getByRole("tab", { name: "Raw" })).toBeInTheDocument();
    // LLM tab is default — shows the assistant text and model
    expect(container.textContent).toContain("Hello from Claude");
    expect(container.textContent).toContain("claude-opus-4-8");
  });

  it("does not add an LLM tab to a plain JSON body", () => {
    const { container } = render(<BodyViewer data='{"key":"value"}' />);
    const view = within(container);
    expect(view.queryByRole("tab", { name: "LLM" })).not.toBeInTheDocument();
    expect(view.getByRole("tab", { name: "Tree" })).toBeInTheDocument();
  });

  it("resets the selected tab when the body changes (no blank panel)", async () => {
    const llmBody = JSON.stringify({
      type: "message",
      role: "assistant",
      model: "claude-opus-4-8",
      content: [{ type: "text", text: "hi" }],
      usage: { input_tokens: 1, output_tokens: 1 },
    });
    const { container, rerender } = render(<BodyViewer data={llmBody} />);
    const view = within(container);
    // Select the 3rd tab (Raw, index 2) on the LLM body.
    await userEvent.click(view.getByRole("tab", { name: "Raw" }));
    // Navigate to a plain JSON body which only has 2 tabs — index 2 would be stale.
    rerender(<BodyViewer data='{"key":"value"}' />);
    // Tab reset to 0 → Tree renders (not a blank panel), and no LLM tab exists.
    expect(view.queryByRole("tab", { name: "LLM" })).not.toBeInTheDocument();
    expect(container.textContent).toContain("key");
    expect(container.textContent).toContain("value");
  });
});
