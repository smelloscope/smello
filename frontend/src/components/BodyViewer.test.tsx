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
});
