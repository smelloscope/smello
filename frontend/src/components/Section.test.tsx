import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import { Provider } from "jotai";
import Section from "./Section";

function renderSection(props: React.ComponentProps<typeof Section>) {
  return render(
    <Provider>
      <Section {...props} />
    </Provider>,
  );
}

describe("Section", () => {
  it("renders headers collapsed by default", () => {
    renderSection({
      title: "Request",
      side: "request",
      headers: { Host: "example.com" },
      body: null,
      bodySize: 0,
    });
    expect(screen.getByText("Headers (1)")).toBeInTheDocument();
    expect(screen.getByText("Host")).not.toBeVisible();
  });

  it("expands headers on click", async () => {
    const { container } = renderSection({
      title: "Request",
      side: "request",
      headers: { Host: "example.com", Accept: "text/html" },
      body: null,
      bodySize: 0,
    });
    const view = within(container);
    await userEvent.click(view.getByText("Headers (2)"));
    expect(view.getByText("Host")).toBeVisible();
    expect(view.getByText("Accept")).toBeVisible();
  });

  it("renders no body panel when body is null", () => {
    renderSection({
      title: "Request",
      side: "request",
      headers: { Host: "example.com" },
      body: null,
      bodySize: 0,
    });
    expect(screen.queryByText(/Body/)).not.toBeInTheDocument();
  });

  it("renders body panel with size when body is present", () => {
    renderSection({
      title: "Response",
      side: "response",
      headers: { "Content-Type": "text/plain" },
      body: "hello",
      bodySize: 5,
    });
    expect(screen.getByText("Response")).toBeInTheDocument();
    expect(screen.getByText("Body (5 bytes)")).toBeInTheDocument();
    expect(screen.getByText("hello")).toBeInTheDocument();
  });
});
