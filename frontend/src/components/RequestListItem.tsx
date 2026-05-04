import { useEffect, useRef } from "react";
import ListItemButton from "@mui/material/ListItemButton";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { mono, dark } from "../theme";
import StatusBadge from "./StatusBadge";
import EventTypeIcon from "./EventTypeIcon";
import type { EventSummary } from "../api/events";

type RequestListItemProps = {
  item: EventSummary;
  selected: boolean;
  onClick: () => void;
};

function formatTime(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleTimeString("en-US", { hour12: false });
}

function HttpRow({ item }: { item: EventSummary }) {
  const match = item.summary.match(/^(\w+)\s+(.+?)\s+→\s+(\d+)$/);
  const method = match?.[1] ?? "???";
  const path = match?.[2] ?? item.summary;
  const status = match?.[3] ? parseInt(match[3], 10) : 0;

  return (
    <Box sx={{ flex: 1, minWidth: 0 }}>
      <Stack direction="row" alignItems="center" spacing={0.75} sx={{ minWidth: 0 }}>
        <Typography
          component="span"
          sx={{
            fontFamily: mono,
            fontSize: 11,
            fontWeight: 700,
            color: dark.textSecondary,
            flexShrink: 0,
          }}
        >
          {method}
        </Typography>
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
          title={item.summary}
        >
          {path}
        </Typography>
      </Stack>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mt: 0.25 }}>
        <Typography
          component="span"
          sx={{ fontSize: 11, color: dark.textSecondary, flex: 1, mr: 1 }}
        >
          {formatTime(item.timestamp)}
        </Typography>
        <StatusBadge status={status} />
      </Stack>
    </Box>
  );
}

function LogRow({ item }: { item: EventSummary }) {
  const match = item.summary.match(/^(\w+)\s+(.+?):\s+(.*)$/);
  const level = match?.[1] ?? "INFO";
  const logger = match?.[2] ?? "";
  const message = match?.[3] ?? item.summary;

  return (
    <Box sx={{ flex: 1, minWidth: 0 }}>
      <Stack direction="row" alignItems="center" spacing={0.75} sx={{ minWidth: 0 }}>
        <Typography
          component="span"
          sx={{
            fontFamily: mono,
            fontSize: 11,
            fontWeight: 700,
            color: dark.textSecondary,
            flexShrink: 0,
          }}
        >
          {level}
        </Typography>
        <Typography
          component="span"
          sx={{
            fontSize: 12,
            fontWeight: 500,
            color: dark.textPrimary,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            flex: 1,
          }}
          title={item.summary}
        >
          {message}
        </Typography>
      </Stack>
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
          {logger}
        </Typography>
        <Typography component="span" sx={{ fontSize: 11, color: dark.textDisabled, flexShrink: 0 }}>
          {formatTime(item.timestamp)}
        </Typography>
      </Stack>
    </Box>
  );
}

function ExceptionRow({ item }: { item: EventSummary }) {
  const colonIdx = item.summary.indexOf(":");
  const excType = colonIdx > 0 ? item.summary.slice(0, colonIdx) : item.summary;
  const excValue = colonIdx > 0 ? item.summary.slice(colonIdx + 2) : "";

  return (
    <Box sx={{ flex: 1, minWidth: 0 }}>
      <Stack direction="row" alignItems="center" spacing={0.75} sx={{ minWidth: 0 }}>
        <Typography
          component="span"
          sx={{
            fontFamily: mono,
            fontSize: 12,
            fontWeight: 600,
            color: "#ef9a9a",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            flex: 1,
          }}
          title={item.summary}
        >
          {excType}
        </Typography>
      </Stack>
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
          {excValue}
        </Typography>
        <Typography component="span" sx={{ fontSize: 11, color: dark.textDisabled, flexShrink: 0 }}>
          {formatTime(item.timestamp)}
        </Typography>
      </Stack>
    </Box>
  );
}

function eventLevel(item: EventSummary): string | undefined {
  if (item.event_type !== "log") return undefined;
  const match = item.summary.match(/^(\w+)\s+/);
  return match?.[1];
}

export default function RequestListItem({ item, selected, onClick }: RequestListItemProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (selected && ref.current) {
      ref.current.scrollIntoView({ block: "nearest" });
    }
  }, [selected]);

  return (
    <ListItemButton
      ref={ref}
      selected={selected}
      onClick={onClick}
      sx={{
        py: 1,
        px: 1.5,
        alignItems: "flex-start",
        gap: 1,
        borderBottom: `1px solid ${dark.border}`,
        "&:hover": { bgcolor: dark.hover },
        "&.Mui-selected": {
          bgcolor: dark.selected,
          "&:hover": { bgcolor: dark.selectedHover },
        },
      }}
    >
      <Box sx={{ pt: 0.25, flexShrink: 0 }}>
        <EventTypeIcon eventType={item.event_type} dark level={eventLevel(item)} size={18} />
      </Box>
      {item.event_type === "http" && <HttpRow item={item} />}
      {item.event_type === "log" && <LogRow item={item} />}
      {item.event_type === "exception" && <ExceptionRow item={item} />}
    </ListItemButton>
  );
}
