import type { HotkeyEntry } from "./types";

export const HOTKEYS: HotkeyEntry[] = [
  // General
  { keys: "shift+/", label: "?", description: "Show keyboard shortcuts", group: "General" },
  { keys: "/", label: "/", description: "Focus search", group: "General" },
  { keys: "escape", label: "Esc", description: "Dismiss / blur / deselect", group: "General" },

  // Navigation
  { keys: "j", label: "j", description: "Next request", group: "Navigation" },
  { keys: "ArrowDown", label: "\u2193", description: "Next request", group: "Navigation" },
  { keys: "k", label: "k", description: "Previous request", group: "Navigation" },
  { keys: "ArrowUp", label: "\u2191", description: "Previous request", group: "Navigation" },
  { keys: "backspace", label: "\u232B", description: "Clear selection", group: "Navigation" },

  // Filters
  { keys: "shift+x", label: "Shift+X", description: "Clear all filters", group: "Filters" },

  // Detail
  { keys: "q", label: "q", description: "Toggle query parameters", group: "Detail" },
  { keys: "h", label: "h", description: "Toggle request headers", group: "Detail" },
  { keys: "shift+h", label: "H", description: "Toggle response headers", group: "Detail" },
  { keys: "b", label: "b", description: "Toggle request body", group: "Detail" },
  { keys: "shift+b", label: "B", description: "Toggle response body", group: "Detail" },
  { keys: "c", label: "c", description: "Copy request body", group: "Detail" },
  { keys: "shift+c", label: "C", description: "Copy response body", group: "Detail" },
];
