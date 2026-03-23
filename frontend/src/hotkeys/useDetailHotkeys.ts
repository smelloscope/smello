import { useSetAtom } from "jotai";
import { useHotkeys } from "react-hotkeys-hook";
import { useSelectedRequestId } from "../hooks/useSelectedRequestId";
import { useGetRequestApiRequestsRequestIdGet } from "../api/generated/default/default";
import { headersOpenAtom, bodyOpenAtom, queryParamsOpenAtom } from "../atoms/sectionState";
import { snackbarMessageAtom } from "../atoms/snackbar";

export function useDetailHotkeys() {
  const [selectedId] = useSelectedRequestId();
  const enabled = !!selectedId;

  const { data: detail } = useGetRequestApiRequestsRequestIdGet(selectedId ?? "", {
    query: { enabled },
  });

  const setReqHeaders = useSetAtom(headersOpenAtom.request);
  const setResHeaders = useSetAtom(headersOpenAtom.response);
  const setReqBody = useSetAtom(bodyOpenAtom.request);
  const setResBody = useSetAtom(bodyOpenAtom.response);
  const setQueryParams = useSetAtom(queryParamsOpenAtom.request);
  const setSnackbar = useSetAtom(snackbarMessageAtom);

  // Section toggles
  useHotkeys("q", () => setQueryParams((o) => !o), { enabled });
  useHotkeys("h", () => setReqHeaders((o) => !o), { enabled });
  useHotkeys("shift+h", () => setResHeaders((o) => !o), { enabled });
  useHotkeys("b", () => setReqBody((o) => !o), { enabled });
  useHotkeys("shift+b", () => setResBody((o) => !o), { enabled });

  // Copy shortcuts
  useHotkeys(
    "c",
    () => {
      if (detail?.request_body) {
        navigator.clipboard.writeText(detail.request_body);
        setSnackbar("Request body copied");
      }
    },
    { enabled },
  );

  useHotkeys(
    "shift+c",
    () => {
      if (detail?.response_body) {
        navigator.clipboard.writeText(detail.response_body);
        setSnackbar("Response body copied");
      }
    },
    { enabled },
  );
}
