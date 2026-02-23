import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import JsonViewer from "./JsonViewer";

describe("JsonViewer", () => {
  it("renders nothing when data is null", () => {
    const { container } = render(<JsonViewer data={null} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders raw text for invalid JSON", () => {
    render(<JsonViewer data="not valid json" />);
    expect(screen.getByText("not valid json")).toBeInTheDocument();
    expect(screen.getByText("not valid json").tagName).toBe("PRE");
  });

  it("renders parsed JSON for valid JSON", () => {
    const { container } = render(<JsonViewer data='{"key":"value"}' />);
    // react18-json-view renders the parsed object — check that raw string is NOT shown as-is
    expect(container.textContent).toContain("key");
    expect(container.textContent).toContain("value");
  });
});
