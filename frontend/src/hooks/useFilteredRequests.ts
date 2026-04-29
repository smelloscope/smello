import { useAtomValue } from "jotai";
import {
  hostFilterAtom,
  methodFilterAtom,
  searchFilterAtom,
  eventTypeFilterAtom,
} from "../atoms/filters";
import { useListEvents } from "../api/events";

export function useFilteredRequests() {
  const host = useAtomValue(hostFilterAtom);
  const method = useAtomValue(methodFilterAtom);
  const search = useAtomValue(searchFilterAtom);
  const eventType = useAtomValue(eventTypeFilterAtom);

  return useListEvents(
    {
      ...(eventType ? { event_type: eventType } : {}),
      ...(host ? { host } : {}),
      ...(method ? { method } : {}),
      ...(search ? { search } : {}),
    },
    { refetchInterval: 3_000 },
  );
}
