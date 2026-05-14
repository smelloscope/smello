import { useState } from "react";
import JsonView from "react18-json-view";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import ButtonBase from "@mui/material/ButtonBase";
import Typography from "@mui/material/Typography";
import Collapse from "@mui/material/Collapse";
import ExpandMore from "@mui/icons-material/ExpandMore";
import { customizeNode } from "../annotations";
import { mono } from "../theme";

export type SseEvent = {
  event?: string;
  data?: string;
  id?: string;
  comments: string[];
};

export function parseSseEvents(raw: string): SseEvent[] | null {
  const lines = raw.split("\n");
  const events: SseEvent[] = [];
  let current: SseEvent = { comments: [] };
  let hasContent = false;
  let sseLineCount = 0;

  for (const line of lines) {
    if (line === "") {
      if (hasContent) {
        events.push(current);
        current = { comments: [] };
        hasContent = false;
      }
      continue;
    }

    if (line.startsWith(":")) {
      current.comments.push(line.slice(1).trim());
      hasContent = true;
      sseLineCount++;
      continue;
    }

    const colonIdx = line.indexOf(":");
    if (colonIdx === -1) continue;

    const field = line.slice(0, colonIdx);
    const value = line.slice(colonIdx + 1).replace(/^ /, "");

    if (field === "event") {
      current.event = current.event ? current.event + "\n" + value : value;
      sseLineCount++;
    } else if (field === "data") {
      current.data = current.data ? current.data + "\n" + value : value;
      sseLineCount++;
    } else if (field === "id") {
      current.id = value;
      sseLineCount++;
    }
    hasContent = true;
  }

  if (hasContent) {
    events.push(current);
  }

  if (events.length < 2 || sseLineCount < 3) return null;
  return events;
}

const eventColors: Record<string, string> = {
  message_start: "#1976d2",
  message_delta: "#1976d2",
  message_stop: "#1976d2",
  content_block_start: "#7b1fa2",
  content_block_delta: "#7b1fa2",
  content_block_stop: "#7b1fa2",
  ping: "#757575",
  error: "#d32f2f",
};

function getEventColor(event?: string): string {
  if (!event) return "#757575";
  return eventColors[event] ?? "#0d7c66";
}

function tryParseJson(data: string): unknown | null {
  try {
    return JSON.parse(data);
  } catch {
    return null;
  }
}

function SseEventRow({ event, index }: { event: SseEvent; index: number }) {
  const [open, setOpen] = useState(false);
  const parsedJson = event.data ? tryParseJson(event.data) : null;
  const hasPlainText = parsedJson === null && !!event.data;
  const hasExpandableContent = parsedJson !== null || hasPlainText;
  const color = getEventColor(event.event);

  return (
    <Box
      sx={{
        borderBottom: "1px solid",
        borderColor: "divider",
        "&:last-child": { borderBottom: "none" },
      }}
    >
      <ButtonBase
        disableRipple
        onClick={() => hasExpandableContent && setOpen((o) => !o)}
        sx={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          gap: 1,
          px: 1,
          py: 0.5,
          textAlign: "left",
          cursor: hasExpandableContent ? "pointer" : "default",
          "&:hover": {
            bgcolor: hasExpandableContent ? "action.hover" : "transparent",
          },
        }}
      >
        <Typography
          sx={{
            fontFamily: mono,
            fontSize: 11,
            color: "text.disabled",
            width: 24,
            flexShrink: 0,
            textAlign: "right",
          }}
        >
          {index + 1}
        </Typography>

        {hasExpandableContent && (
          <ExpandMore
            sx={{
              fontSize: 16,
              color: "text.secondary",
              transform: open ? "rotate(180deg)" : "rotate(-90deg)",
              transition: "transform 150ms",
              flexShrink: 0,
            }}
          />
        )}
        {!hasExpandableContent && <Box sx={{ width: 16, flexShrink: 0 }} />}

        <Chip
          label={event.event ?? "message"}
          size="small"
          sx={{
            fontFamily: mono,
            fontSize: 11,
            height: 20,
            fontWeight: 600,
            bgcolor: color,
            color: "#fff",
            flexShrink: 0,
            "& .MuiChip-label": { px: 0.75 },
          }}
        />

        <Typography
          sx={{
            fontFamily: mono,
            fontSize: 12,
            color: "text.secondary",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            flex: 1,
          }}
        >
          {event.data ?? ""}
        </Typography>
      </ButtonBase>

      {hasExpandableContent && (
        <Collapse in={open}>
          <Box sx={{ pl: 7.5, pr: 1, pb: 1, fontSize: 13, fontFamily: mono }}>
            {parsedJson !== null ? (
              <JsonView src={parsedJson} collapsed={2} customizeNode={customizeNode} />
            ) : (
              <Typography
                component="pre"
                sx={{
                  fontFamily: mono,
                  fontSize: 13,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-all",
                  m: 0,
                  color: "text.primary",
                }}
              >
                {event.data}
              </Typography>
            )}
          </Box>
        </Collapse>
      )}
    </Box>
  );
}

export default function SseViewer({ events }: { events: SseEvent[] }) {
  return (
    <Box
      sx={{
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 1,
        overflow: "hidden",
      }}
    >
      {events.map((event, i) => (
        <SseEventRow key={i} event={event} index={i} />
      ))}
    </Box>
  );
}
