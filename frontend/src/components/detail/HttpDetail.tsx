import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import StatusBadge from "../StatusBadge";
import MethodBadge from "../MethodBadge";
import Section from "../Section";
import { parseDisplayUrl, parseQueryParams } from "../../utils/url";
import type { EventDetail, HttpEventData } from "../../api/events";

const mono = "'SF Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace";

export default function HttpDetail({ detail }: { detail: EventDetail }) {
  const d = detail.data as unknown as HttpEventData;
  const { host, path } = parseDisplayUrl(d.url);
  const queryParams = parseQueryParams(d.url);

  return (
    <Box sx={{ p: 2, overflowY: "auto" }}>
      <Box sx={{ mb: 2 }}>
        <Stack direction="row" alignItems="baseline" spacing={1} sx={{ mb: 0.5 }}>
          <MethodBadge method={d.method} size="medium" />
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

        <Typography sx={{ fontSize: 12, color: "text.secondary", mb: 1, pl: 0.25 }}>
          {host}
        </Typography>

        <Stack direction="row" alignItems="center" spacing={1} sx={{ flexWrap: "wrap" }}>
          <StatusBadge status={d.status_code} />
          <Chip
            label={`${d.duration_ms}ms`}
            size="small"
            variant="outlined"
            sx={{
              fontFamily: mono,
              fontSize: 12,
              height: 22,
              fontWeight: d.duration_ms >= 2000 ? 600 : 400,
              color: d.duration_ms >= 2000 ? "warning.main" : "text.secondary",
              borderColor: d.duration_ms >= 2000 ? "warning.main" : "divider",
            }}
          />
          <Chip
            label={d.library}
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
        headers={d.request_headers}
        body={d.request_body}
        bodySize={d.request_body_size}
        queryParams={queryParams}
      />

      <Section
        title="Response"
        side="response"
        headers={d.response_headers}
        body={d.response_body}
        bodySize={d.response_body_size}
      />
    </Box>
  );
}
