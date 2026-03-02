import { render, within } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import RequestListItem from "./RequestListItem";

const baseItem = {
  id: "abc-123",
  method: "GET",
  url: "https://api.example.com/users?page=1",
  host: "api.example.com",
  status_code: 200,
  timestamp: "2025-01-15T14:30:45.123Z",
  duration_ms: 42,
};

function renderItem(overrides = {}, onClick = () => {}) {
  const { container } = render(
    <RequestListItem item={{ ...baseItem, ...overrides }} selected={false} onClick={onClick} />,
  );
  // MUI ListItemButton renders as a div with role="button"
  return within(container);
}

describe("RequestListItem", () => {
  it("renders method, path, host, and duration", () => {
    const view = renderItem();
    expect(view.getByText("GET")).toBeInTheDocument();
    // URL is parsed: path shown as hero text, full URL in title attr
    expect(view.getByText("/users?page=1")).toBeInTheDocument();
    expect(view.getByText("api.example.com")).toBeInTheDocument();
    expect(view.getByTitle(baseItem.url)).toBeInTheDocument();
    expect(view.getByText("42ms")).toBeInTheDocument();
  });

  it("formats timestamp as HH:MM:SS in 24-hour format", () => {
    const view = renderItem();
    const timeSpan = view.getByText(/^\d{2}:\d{2}:\d{2}$/);
    expect(timeSpan).toBeInTheDocument();
  });

  it("calls onClick when clicked", () => {
    const onClick = vi.fn();
    const view = renderItem({}, onClick);
    view.getByRole("button").click();
    expect(onClick).toHaveBeenCalledOnce();
  });
});
