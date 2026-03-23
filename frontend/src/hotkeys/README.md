# Keyboard Shortcuts

Smello supports Gmail/Linear-style keyboard shortcuts for fast navigation.
Press `?` anywhere in the app to see all available shortcuts.

## Architecture

```
hotkeys/
  types.ts               -- HotkeyEntry type
  registry.ts            -- Central HOTKEYS array (single source of truth)
  useGlobalHotkeys.ts    -- /, Escape, Shift+X, Backspace, ? bindings
  useListNavigation.ts   -- j/k/ArrowUp/ArrowDown request navigation
  useDetailHotkeys.ts    -- h/H/b/B/q/c/C section toggle + copy
  HotkeyHelpDialog.tsx   -- MUI Dialog listing all shortcuts
```

All three hooks are mounted in `SplitView.tsx`. The help dialog is mounted in `App.tsx`.

### Registry

`registry.ts` exports a `HOTKEYS` array — the single source of truth for both the help dialog and documentation. Each entry has:

- `keys` — the `react-hotkeys-hook` key string (e.g. `"shift+h"`)
- `label` — human-readable display (e.g. `"H"`)
- `description` — what it does
- `group` — category for grouping in the help dialog

### Section state

Section collapse state (headers/body open/closed) lives in jotai atoms (`atoms/sectionState.ts`) so both `Section.tsx` clicks and `useDetailHotkeys` can toggle them. State resets to defaults when the selected request changes.

## Adding a new hotkey

1. Add the entry to `HOTKEYS` in `registry.ts` (this updates the help dialog automatically)
2. Add the `useHotkeys()` call in the appropriate hook (`useGlobalHotkeys`, `useListNavigation`, or `useDetailHotkeys`)
3. If the hotkey needs new shared state, add a jotai atom in `atoms/`

## Library

Uses [react-hotkeys-hook](https://github.com/JohannesKlawornn/react-hotkeys-hook) v5.
Key features used: `preventDefault`, `enabled` (conditional activation), `enableOnFormTags` (for Escape in inputs).
By default, hotkeys are suppressed when `<input>`, `<textarea>`, or `<select>` elements are focused.
