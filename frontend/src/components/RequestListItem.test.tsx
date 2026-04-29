import { render, within } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import RequestListItem from "./RequestListItem";
import type { EventSummary } from "../api/events";

const httpItem: EventSummary = {
  id: "abc-123",
  timestamp: "2025-01-15T14:30:45.123Z",
  event_type: "http",
  summary: "GET /users?page=1 → 200",
};

const logItem: EventSummary = {
  id: "log-123",
  timestamp: "2025-01-15T14:30:45.123Z",
  event_type: "log",
  summary: "WARNING myapp.auth: Token expired for user 42",
};

const exceptionItem: EventSummary = {
  id: "exc-123",
  timestamp: "2025-01-15T14:30:45.123Z",
  event_type: "exception",
  summary: "ValueError: invalid literal for int()",
};

function renderItem(item: EventSummary, onClick = () => {}) {
  const { container } = render(<RequestListItem item={item} selected={false} onClick={onClick} />);
  return within(container);
}

describe("RequestListItem", () => {
  it("renders HTTP event with method and path", () => {
    const view = renderItem(httpItem);
    expect(view.getByText("GET")).toBeInTheDocument();
    expect(view.getByText("/users?page=1")).toBeInTheDocument();
    expect(view.getByText("200")).toBeInTheDocument();
  });

  it("renders log event with level and message", () => {
    const view = renderItem(logItem);
    expect(view.getByText("WARNING")).toBeInTheDocument();
    expect(view.getByText("Token expired for user 42")).toBeInTheDocument();
    expect(view.getByText("myapp.auth")).toBeInTheDocument();
  });

  it("renders exception event with type", () => {
    const view = renderItem(exceptionItem);
    expect(view.getByText("ValueError")).toBeInTheDocument();
  });

  it("formats timestamp as HH:MM:SS in 24-hour format", () => {
    const view = renderItem(httpItem);
    const timeSpan = view.getByText(/^\d{2}:\d{2}:\d{2}$/);
    expect(timeSpan).toBeInTheDocument();
  });

  it("calls onClick when clicked", () => {
    const onClick = vi.fn();
    const view = renderItem(httpItem, onClick);
    view.getByRole("button").click();
    expect(onClick).toHaveBeenCalledOnce();
  });
});
