import { useEffect } from "react";
import { useSetAtom } from "jotai";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import { useGetRequestApiRequestsRequestIdGet } from "../api/generated/default/default";
import StatusBadge from "./StatusBadge";
import MethodBadge from "./MethodBadge";
import Section from "./Section";
import { parseDisplayUrl, parseQueryParams } from "../utils/url";
import { headersOpenAtom, bodyOpenAtom, queryParamsOpenAtom } from "../atoms/sectionState";

const mono = "'SF Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace";

export default function RequestDetail({ requestId }: { requestId: string }) {
  const {
    data: detail,
    isLoading,
    isError,
  } = useGetRequestApiRequestsRequestIdGet(requestId, {
    query: { retry: false },
  });

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

  const { host, path } = parseDisplayUrl(detail.url);
  const queryParams = parseQueryParams(detail.url);

  return (
    <Box sx={{ p: 2, overflowY: "auto" }}>
      <Box sx={{ mb: 2 }}>
        {/* Method + Path */}
        <Stack direction="row" alignItems="baseline" spacing={1} sx={{ mb: 0.5 }}>
          <MethodBadge method={detail.method} size="medium" />
          <Typography
            sx={{
              fontFamily: mono,
              fontSize: 14,
              fontWeight: 500,
              wordBreak: "break-all",
              flex: 1,
            }}
          >
            {path}
          </Typography>
        </Stack>

        {/* Host */}
        <Typography
          sx={{
            fontSize: 12,
            color: "text.secondary",
            mb: 1,
            pl: 0.25,
          }}
        >
          {host}
        </Typography>

        {/* Metadata row */}
        <Stack direction="row" alignItems="center" spacing={1} sx={{ flexWrap: "wrap" }}>
          <StatusBadge status={detail.status_code} />
          <Chip
            label={`${detail.duration_ms}ms`}
            size="small"
            variant="outlined"
            sx={{
              fontFamily: mono,
              fontSize: 12,
              height: 22,
              fontWeight: detail.duration_ms >= 2000 ? 600 : 400,
              color: detail.duration_ms >= 2000 ? "warning.main" : "text.secondary",
              borderColor: detail.duration_ms >= 2000 ? "warning.main" : "divider",
            }}
          />
          <Chip
            label={detail.library}
            size="small"
            variant="outlined"
            sx={{ fontSize: 12, height: 22, color: "text.secondary", borderColor: "divider" }}
          />
          <Typography variant="body2" color="text.disabled" sx={{ fontSize: 12 }}>
            {new Date(detail.timestamp).toLocaleString()}
          </Typography>
        </Stack>
      </Box>

      <Divider sx={{ mb: 2 }} />

      <Section
        title="Request"
        side="request"
        headers={detail.request_headers}
        body={detail.request_body}
        bodySize={detail.request_body_size}
        queryParams={queryParams}
      />

      <Section
        title="Response"
        side="response"
        headers={detail.response_headers}
        body={detail.response_body}
        bodySize={detail.response_body_size}
      />
    </Box>
  );
}
