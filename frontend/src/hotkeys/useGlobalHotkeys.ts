import { useAtom, useSetAtom } from "jotai";
import { useHotkeys } from "react-hotkeys-hook";
import {
  hostFilterAtom,
  methodFilterAtom,
  searchFilterAtom,
  eventTypeFilterAtom,
  appFilterAtom,
  sessionFilterAtom,
} from "../atoms/filters";
import { hotkeyHelpOpenAtom } from "../atoms/hotkeyHelp";
import { useSelectedRequestId } from "../hooks/useSelectedRequestId";

export function useGlobalHotkeys() {
  const setHost = useSetAtom(hostFilterAtom);
  const setMethod = useSetAtom(methodFilterAtom);
  const setSearch = useSetAtom(searchFilterAtom);
  const setEventType = useSetAtom(eventTypeFilterAtom);
  const setApp = useSetAtom(appFilterAtom);
  const setSession = useSetAtom(sessionFilterAtom);
  const [helpOpen, setHelpOpen] = useAtom(hotkeyHelpOpenAtom);
  const [selectedId, setSelectedId] = useSelectedRequestId();

  // ? = toggle help (useKey matches event.key, works across keyboard layouts)
  useHotkeys("?", () => setHelpOpen((o) => !o), { useKey: true });

  // / = focus search
  useHotkeys(
    "/",
    (e) => {
      e.preventDefault();
      document.querySelector<HTMLInputElement>("[data-hotkey-target='search']")?.focus();
    },
    { useKey: true },
  );

  // Escape = cascading dismiss
  useHotkeys(
    "escape",
    () => {
      if (helpOpen) {
        setHelpOpen(false);
        return;
      }
      if (document.activeElement instanceof HTMLInputElement) {
        document.activeElement.blur();
        return;
      }
      if (selectedId) {
        setSelectedId(null);
      }
    },
    { enableOnFormTags: ["INPUT", "SELECT"] },
  );

  // Shift+X = clear all filters
  useHotkeys("shift+x", () => {
    setHost("");
    setMethod("");
    setSearch("");
    setEventType("");
    setApp(undefined);
    setSession(undefined);
  });

  // Backspace = deselect
  useHotkeys("backspace", () => {
    if (selectedId) setSelectedId(null);
  });
}
