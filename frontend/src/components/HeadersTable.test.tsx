import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import HeadersTable from "./HeadersTable";

describe("HeadersTable", () => {
  it("renders nothing for empty headers", () => {
    const { container } = render(<HeadersTable headers={{}} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders a row for each header", () => {
    render(<HeadersTable headers={{ "Content-Type": "application/json", Accept: "text/html" }} />);
    expect(screen.getByText("Content-Type")).toBeInTheDocument();
    expect(screen.getByText("application/json")).toBeInTheDocument();
    expect(screen.getByText("Accept")).toBeInTheDocument();
    expect(screen.getByText("text/html")).toBeInTheDocument();
  });
});
