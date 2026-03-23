import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import { Provider, createStore } from "jotai";
import { hotkeyHelpOpenAtom } from "../../atoms/hotkeyHelp";
import HotkeyHelpDialog from "../HotkeyHelpDialog";

function renderDialog(open = false) {
  const store = createStore();
  store.set(hotkeyHelpOpenAtom, open);
  return {
    store,
    ...render(
      <Provider store={store}>
        <HotkeyHelpDialog />
      </Provider>,
    ),
  };
}

describe("HotkeyHelpDialog", () => {
  it("is hidden when atom is false", () => {
    renderDialog(false);
    expect(screen.queryByText("Keyboard Shortcuts")).not.toBeInTheDocument();
  });

  it("renders all groups when open", () => {
    renderDialog(true);
    expect(screen.getByText("Keyboard Shortcuts")).toBeInTheDocument();
    expect(screen.getByText("General")).toBeInTheDocument();
    expect(screen.getByText("Navigation")).toBeInTheDocument();
    expect(screen.getByText("Filters")).toBeInTheDocument();
    expect(screen.getByText("Detail")).toBeInTheDocument();
  });

  it("lists shortcut descriptions", () => {
    renderDialog(true);
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText("Show keyboard shortcuts")).toBeInTheDocument();
    expect(within(dialog).getByText("Focus search")).toBeInTheDocument();
    expect(within(dialog).getByText("Next request")).toBeInTheDocument();
    expect(within(dialog).getByText("Toggle request headers")).toBeInTheDocument();
  });

  it("closes when close button is clicked", async () => {
    const { store } = renderDialog(true);
    const closeButton = screen.getByRole("button");
    await userEvent.click(closeButton);
    expect(store.get(hotkeyHelpOpenAtom)).toBe(false);
  });
});
