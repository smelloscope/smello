export type HotkeyGroup = "Navigation" | "Filters" | "Detail" | "General" | "Actions";

export type HotkeyEntry = {
  keys: string;
  label: string;
  description: string;
  group: HotkeyGroup;
};
