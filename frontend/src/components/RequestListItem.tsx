import ListItemButton from "@mui/material/ListItemButton";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { mono, dark } from "../theme";
import StatusBadge from "./StatusBadge";
import MethodBadge from "./MethodBadge";
import { parseDisplayUrl } from "../utils/url";
import type { RequestSummary } from "../api/generated/model";

type RequestListItemProps = {
  item: RequestSummary;
  selected: boolean;
  onClick: () => void;
};

function formatTime(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleTimeString("en-US", { hour12: false });
}

function formatDuration(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${ms}ms`;
}

export default function RequestListItem({ item, selected, onClick }: RequestListItemProps) {
  const { host, path } = parseDisplayUrl(item.url);
  const isGrpc = item.url.startsWith("grpc://");

  return (
    <ListItemButton
      selected={selected}
      onClick={onClick}
      sx={{
        py: 1,
        px: 1.5,
        alignItems: "flex-start",
        borderBottom: `1px solid ${dark.border}`,
        "&:hover": {
          bgcolor: dark.hover,
        },
        "&.Mui-selected": {
          bgcolor: dark.selected,
          "&:hover": {
            bgcolor: dark.selectedHover,
          },
        },
      }}
    >
      <Box sx={{ flex: 1, minWidth: 0 }}>
        {/* Row 1: Method + path */}
        <Stack direction="row" alignItems="center" spacing={0.75} sx={{ minWidth: 0 }}>
          <MethodBadge method={item.method} dark />
          <Typography
            component="span"
            sx={{
              fontFamily: mono,
              fontSize: 12,
              fontWeight: 500,
              color: dark.textPrimary,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              flex: 1,
            }}
            title={item.url}
          >
            {path}
          </Typography>
        </Stack>

        {/* Row 2: host + metadata */}
        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mt: 0.25 }}>
          <Typography
            component="span"
            sx={{
              fontSize: 11,
              color: dark.textSecondary,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              flex: 1,
              mr: 1,
            }}
          >
            {host}
            {isGrpc && (
              <Typography
                component="span"
                sx={{
                  fontSize: 10,
                  color: dark.textDisabled,
                  ml: 0.5,
                }}
              >
                gRPC
              </Typography>
            )}
          </Typography>
          <Stack direction="row" alignItems="center" spacing={0.75} sx={{ flexShrink: 0 }}>
            <Typography
              component="span"
              sx={{
                fontSize: 11,
                color: item.duration_ms >= 2000 ? "#ffa726" : dark.textDisabled,
                fontFamily: mono,
                fontWeight: item.duration_ms >= 2000 ? 600 : 400,
              }}
            >
              {formatDuration(item.duration_ms)}
            </Typography>
            <Typography component="span" sx={{ fontSize: 11, color: dark.textDisabled }}>
              {formatTime(item.timestamp)}
            </Typography>
            <StatusBadge status={item.status_code} />
          </Stack>
        </Stack>
      </Box>
    </ListItemButton>
  );
}
