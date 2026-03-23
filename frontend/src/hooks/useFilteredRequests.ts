import { useAtomValue } from "jotai";
import { hostFilterAtom, methodFilterAtom, searchFilterAtom } from "../atoms/filters";
import { useListRequestsApiRequestsGet } from "../api/generated/default/default";

export function useFilteredRequests() {
  const host = useAtomValue(hostFilterAtom);
  const method = useAtomValue(methodFilterAtom);
  const search = useAtomValue(searchFilterAtom);

  return useListRequestsApiRequestsGet(
    {
      ...(host ? { host } : {}),
      ...(method ? { method } : {}),
      ...(search ? { search } : {}),
    },
    {
      query: { refetchInterval: 3_000 },
    },
  );
}
