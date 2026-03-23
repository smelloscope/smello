import { useCallback } from "react";
import { useHotkeys } from "react-hotkeys-hook";
import { useSelectedRequestId } from "../hooks/useSelectedRequestId";
import { useFilteredRequests } from "../hooks/useFilteredRequests";

export function useListNavigation() {
  const { data: requests = [] } = useFilteredRequests();
  const [selectedId, setSelectedId] = useSelectedRequestId();

  const navigate = useCallback(
    (direction: 1 | -1) => {
      if (requests.length === 0) return;
      const currentIndex = selectedId ? requests.findIndex((r) => r.id === selectedId) : -1;
      let nextIndex: number;
      if (currentIndex === -1) {
        nextIndex = direction === 1 ? 0 : requests.length - 1;
      } else {
        nextIndex = currentIndex + direction;
        if (nextIndex < 0) nextIndex = 0;
        if (nextIndex >= requests.length) nextIndex = requests.length - 1;
      }
      setSelectedId(requests[nextIndex]!.id);
    },
    [requests, selectedId, setSelectedId],
  );

  useHotkeys("j, ArrowDown", () => navigate(1), { preventDefault: true });
  useHotkeys("k, ArrowUp", () => navigate(-1), { preventDefault: true });
}
