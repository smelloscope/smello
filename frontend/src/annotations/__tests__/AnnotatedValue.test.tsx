import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AnnotatedValue from "../AnnotatedValue";
import { TimestampAnnotation } from "../timestamp";

const annotation = new TimestampAnnotation(1705312245, "unix-seconds");

describe("AnnotatedValue", () => {
  it("renders a number with json-view--number class", () => {
    const { container } = render(<AnnotatedValue value={42} annotation={annotation} />);
    const span = container.querySelector(".json-view--number");
    expect(span).not.toBeNull();
    expect(span!.textContent).toBe("42");
  });

  it("renders a string with json-view--string class and quotes", () => {
    const { container } = render(<AnnotatedValue value="hello" annotation={annotation} />);
    const span = container.querySelector(".json-view--string");
    expect(span).not.toBeNull();
    expect(span!.textContent).toBe('"hello"');
  });

  it("renders a boolean with json-view--boolean class", () => {
    const { container } = render(<AnnotatedValue value={true} annotation={annotation} />);
    expect(container.querySelector(".json-view--boolean")).not.toBeNull();
  });

  it("renders null with json-view--null class", () => {
    const { container } = render(<AnnotatedValue value={null} annotation={annotation} />);
    expect(container.querySelector(".json-view--null")).not.toBeNull();
  });

  it("renders a tooltip icon", () => {
    const { container } = render(<AnnotatedValue value={42} annotation={annotation} />);
    expect(container.querySelector("svg")).not.toBeNull();
  });

  it("shows annotation content on hover", async () => {
    render(<AnnotatedValue value={42} annotation={annotation} />);
    const icon = document.querySelector("svg")!;
    await userEvent.hover(icon);
    expect(await screen.findByRole("tooltip")).toHaveTextContent("2024-01-15 09:50:45 UTC");
  });
});
