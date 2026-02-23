import ListItemButton from "@mui/material/ListItemButton";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import StatusBadge from "./StatusBadge";
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

export default function RequestListItem({ item, selected, onClick }: RequestListItemProps) {
  return (
    <ListItemButton
      selected={selected}
      onClick={onClick}
      sx={{
        py: 0.75,
        px: 1.5,
        borderBottom: "1px solid",
        borderColor: "divider",
        alignItems: "flex-start",
      }}
    >
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Stack direction="row" alignItems="center" spacing={0.75} sx={{ mb: 0.25 }}>
          <Typography
            component="span"
            sx={{
              fontWeight: 700,
              fontSize: 12,
              fontFamily: "monospace",
              minWidth: 44,
            }}
          >
            {item.method}
          </Typography>
          <StatusBadge status={item.status_code} />
        </Stack>
        <Typography
          variant="body2"
          sx={{
            fontFamily: "monospace",
            fontSize: 12,
            color: "text.secondary",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
          title={item.url}
        >
          {item.url}
        </Typography>
        <Stack direction="row" spacing={1} sx={{ mt: 0.25, color: "text.disabled", fontSize: 11 }}>
          <span>{formatTime(item.timestamp)}</span>
          <span>{item.duration_ms}ms</span>
        </Stack>
      </Box>
    </ListItemButton>
  );
}
