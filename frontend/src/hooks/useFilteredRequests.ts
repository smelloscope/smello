import { useAtomValue } from "jotai";
import {
  hostFilterAtom,
  methodFilterAtom,
  searchFilterAtom,
  eventTypeFilterAtom,
  appFilterAtom,
  sessionFilterAtom,
} from "../atoms/filters";
import { useListEvents } from "../api/events";

export function useFilteredRequests() {
  const host = useAtomValue(hostFilterAtom);
  const method = useAtomValue(methodFilterAtom);
  const search = useAtomValue(searchFilterAtom);
  const eventType = useAtomValue(eventTypeFilterAtom);
  const app = useAtomValue(appFilterAtom);
  const session = useAtomValue(sessionFilterAtom);

  return useListEvents(
    {
      ...(eventType ? { event_type: eventType } : {}),
      ...(host ? { host } : {}),
      ...(method ? { method } : {}),
      ...(search ? { search } : {}),
      ...(app !== undefined ? { app } : {}),
      ...(session !== undefined ? { session } : {}),
    },
    { refetchInterval: 3_000 },
  );
}
