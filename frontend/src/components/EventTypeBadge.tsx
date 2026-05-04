import Chip from "@mui/material/Chip";
import { mono } from "../theme";
import type { EventType } from "../api/events";

const colorsLight: Record<string, { color: string; bg: string }> = {
  http: { color: "#1565c0", bg: "#e3f2fd" },
  log: { color: "#e65100", bg: "#fff3e0" },
  exception: { color: "#c62828", bg: "#ffebee" },
};

const colorsDark: Record<string, { color: string; bg: string }> = {
  http: { color: "#64b5f6", bg: "rgba(100,181,246,0.12)" },
  log: { color: "#ffb74d", bg: "rgba(255,183,77,0.12)" },
  exception: { color: "#ef9a9a", bg: "rgba(239,154,154,0.15)" },
};

const labels: Record<string, string> = {
  http: "HTTP",
  log: "LOG",
  exception: "ERR",
};

type Props = {
  eventType: EventType;
  dark?: boolean;
};

export default function EventTypeBadge({ eventType, dark = false }: Props) {
  const palette = dark ? colorsDark : colorsLight;
  const { color, bg } = palette[eventType] ?? palette.http!;

  return (
    <Chip
      label={labels[eventType] ?? eventType.toUpperCase()}
      size="small"
      sx={{
        fontFamily: mono,
        fontWeight: 700,
        fontSize: 10,
        height: 20,
        minWidth: 36,
        color,
        bgcolor: bg,
        borderRadius: 1,
      }}
    />
  );
}
