import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import Paper from "@mui/material/Paper";
import LogLevelBadge from "../LogLevelBadge";
import BodyViewer from "../BodyViewer";
import type { EventDetail, LogEventData } from "../../api/events";

const mono = "'SF Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace";

export default function LogDetail({ detail }: { detail: EventDetail }) {
  const d = detail.data as unknown as LogEventData;
  const hasExtra = d.extra && Object.keys(d.extra).length > 0;

  return (
    <Box sx={{ p: 2, overflowY: "auto" }}>
      <Box sx={{ mb: 2 }}>
        <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
          <LogLevelBadge level={d.level} />
          <Typography sx={{ fontFamily: mono, fontSize: 14, fontWeight: 600 }}>
            {d.logger_name}
          </Typography>
        </Stack>

        <Typography
          sx={{
            fontSize: 14,
            mb: 1.5,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {d.message}
        </Typography>

        <Stack direction="row" alignItems="center" spacing={1} sx={{ flexWrap: "wrap" }}>
          {d.pathname && d.lineno && (
            <Chip
              label={`${d.pathname}:${d.lineno}`}
              size="small"
              variant="outlined"
              sx={{
                fontFamily: mono,
                fontSize: 11,
                height: 22,
                color: "text.secondary",
                borderColor: "divider",
              }}
            />
          )}
          {d.func_name && (
            <Chip
              label={d.func_name}
              size="small"
              variant="outlined"
              sx={{
                fontFamily: mono,
                fontSize: 11,
                height: 22,
                color: "text.secondary",
                borderColor: "divider",
              }}
            />
          )}
          <Typography variant="body2" color="text.disabled" sx={{ fontSize: 12 }}>
            {new Date(detail.timestamp).toLocaleString()}
          </Typography>
        </Stack>
      </Box>

      {d.exc_text && (
        <>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 0.5 }}>
            Exception
          </Typography>
          <Paper
            variant="outlined"
            sx={{
              p: 1.5,
              mb: 2,
              bgcolor: "rgba(239,154,154,0.04)",
              borderColor: "rgba(239,154,154,0.2)",
            }}
          >
            <Typography
              component="pre"
              sx={{
                fontFamily: mono,
                fontSize: 12,
                m: 0,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                color: "#ef9a9a",
              }}
            >
              {d.exc_text}
            </Typography>
          </Paper>
        </>
      )}

      {hasExtra && (
        <>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 0.5 }}>
            Extra
          </Typography>
          <Paper variant="outlined" sx={{ p: 1 }}>
            <BodyViewer data={JSON.stringify(d.extra, null, 2)} />
          </Paper>
        </>
      )}
    </Box>
  );
}
