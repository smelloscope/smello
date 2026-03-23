export type HotkeyGroup = "Navigation" | "Filters" | "Detail" | "General";

export type HotkeyEntry = {
  keys: string;
  label: string;
  description: string;
  group: HotkeyGroup;
};
