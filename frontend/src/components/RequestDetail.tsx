import { useEffect } from "react";
import { useSetAtom } from "jotai";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { useGetEvent } from "../api/events";
import HttpDetail from "./detail/HttpDetail";
import LogDetail from "./detail/LogDetail";
import ExceptionDetail from "./detail/ExceptionDetail";
import { headersOpenAtom, bodyOpenAtom, queryParamsOpenAtom } from "../atoms/sectionState";

export default function RequestDetail({ requestId }: { requestId: string }) {
  const { data: detail, isLoading, isError } = useGetEvent(requestId, { retry: false });

  // Reset section collapse state when switching requests
  const setReqHeaders = useSetAtom(headersOpenAtom.request);
  const setResHeaders = useSetAtom(headersOpenAtom.response);
  const setReqBody = useSetAtom(bodyOpenAtom.request);
  const setResBody = useSetAtom(bodyOpenAtom.response);
  const setQueryParams = useSetAtom(queryParamsOpenAtom.request);

  useEffect(() => {
    setReqHeaders(false);
    setResHeaders(false);
    setReqBody(true);
    setResBody(true);
    setQueryParams(false);
  }, [requestId, setReqHeaders, setResHeaders, setReqBody, setResBody, setQueryParams]);

  useEffect(() => {
    if (isError) {
      window.location.hash = "";
    }
  }, [isError]);

  if (isLoading) {
    return (
      <Box sx={{ p: 3, color: "text.secondary" }}>
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  if (isError || !detail) {
    return null;
  }

  // Narrow on the discriminator inside `data` so TS refines `detail.data` for
  // each branch.
  switch (detail.data.event_type) {
    case "http":
      return <HttpDetail detail={{ ...detail, data: detail.data }} />;
    case "log":
      return <LogDetail detail={{ ...detail, data: detail.data }} />;
    case "exception":
      return <ExceptionDetail detail={{ ...detail, data: detail.data }} />;
    default:
      return (
        <Box sx={{ p: 3, color: "text.secondary" }}>
          <Typography>Unknown event type: {detail.event_type}</Typography>
        </Box>
      );
  }
}
