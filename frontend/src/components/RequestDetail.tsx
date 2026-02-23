import { useEffect } from "react";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Divider from "@mui/material/Divider";
import { useGetRequestApiRequestsRequestIdGet } from "../api/generated/default/default";
import StatusBadge from "./StatusBadge";
import Section from "./Section";

export default function RequestDetail({ requestId }: { requestId: string }) {
  const {
    data: detail,
    isLoading,
    isError,
  } = useGetRequestApiRequestsRequestIdGet(requestId, {
    query: { retry: false },
  });

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

  return (
    <Box sx={{ p: 2, overflowY: "auto" }}>
      <Box sx={{ mb: 2 }}>
        <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 0.5 }}>
          <Typography sx={{ fontWeight: 700, fontFamily: "monospace", fontSize: 16 }}>
            {detail.method}
          </Typography>
          <Typography
            sx={{
              fontFamily: "monospace",
              fontSize: 14,
              wordBreak: "break-all",
              flex: 1,
            }}
          >
            {detail.url}
          </Typography>
        </Stack>
        <Stack direction="row" alignItems="center" spacing={1.5} sx={{ flexWrap: "wrap" }}>
          <StatusBadge status={detail.status_code} />
          <Typography variant="body2" color="text.secondary">
            {detail.duration_ms}ms
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {detail.library}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {new Date(detail.timestamp).toLocaleString()}
          </Typography>
        </Stack>
      </Box>

      <Divider sx={{ mb: 2 }} />

      <Section
        title="Request"
        headers={detail.request_headers}
        body={detail.request_body}
        bodySize={detail.request_body_size}
      />

      <Section
        title="Response"
        headers={detail.response_headers}
        body={detail.response_body}
        bodySize={detail.response_body_size}
      />
    </Box>
  );
}
