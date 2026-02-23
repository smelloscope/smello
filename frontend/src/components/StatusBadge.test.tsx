import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import StatusBadge from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders the status code as text", () => {
    render(<StatusBadge status={200} />);
    expect(screen.getByText("200")).toBeInTheDocument();
  });

  it.each([
    [200, "success"],
    [201, "success"],
    [299, "success"],
    [301, "info"],
    [304, "info"],
    [400, "warning"],
    [404, "warning"],
    [500, "error"],
    [503, "error"],
  ] as const)("maps status %d to MUI color %s", (status, expectedColor) => {
    const { container } = render(<StatusBadge status={status} />);
    const chip = container.querySelector(".MuiChip-root") as HTMLElement;
    const capitalized = expectedColor.charAt(0).toUpperCase() + expectedColor.slice(1);
    expect(chip.className).toContain(`MuiChip-color${capitalized}`);
  });
});
