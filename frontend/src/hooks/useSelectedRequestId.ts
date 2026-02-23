import { useCallback, useSyncExternalStore } from "react";

function getSnapshot(): string | null {
  const hash = window.location.hash.slice(1);
  return hash || null;
}

function subscribe(callback: () => void): () => void {
  window.addEventListener("hashchange", callback);
  return () => window.removeEventListener("hashchange", callback);
}

export function useSelectedRequestId() {
  const id = useSyncExternalStore(subscribe, getSnapshot);

  const setId = useCallback((nextId: string | null) => {
    window.location.hash = nextId ?? "";
  }, []);

  return [id, setId] as const;
}
