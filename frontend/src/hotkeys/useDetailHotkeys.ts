import { useSetAtom } from "jotai";
import { useHotkeys } from "react-hotkeys-hook";
import { useSelectedRequestId } from "../hooks/useSelectedRequestId";
import { useGetEvent } from "../api/events";
import { headersOpenAtom, bodyOpenAtom, queryParamsOpenAtom } from "../atoms/sectionState";
import { snackbarMessageAtom } from "../atoms/snackbar";

export function useDetailHotkeys() {
  const [selectedId] = useSelectedRequestId();
  const enabled = !!selectedId;

  const { data: detail } = useGetEvent(selectedId ?? "", {
    enabled,
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

  // Copy shortcuts (only for HTTP events)
  useHotkeys(
    "c",
    () => {
      if (detail?.data.event_type === "http") {
        const { request_body } = detail.data;
        if (request_body) {
          navigator.clipboard.writeText(request_body);
          setSnackbar("Request body copied");
        }
      }
    },
    { enabled },
  );

  useHotkeys(
    "shift+c",
    () => {
      if (detail?.data.event_type === "http") {
        const { response_body } = detail.data;
        if (response_body) {
          navigator.clipboard.writeText(response_body);
          setSnackbar("Response body copied");
        }
      }
    },
    { enabled },
  );
}
