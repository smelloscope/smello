import SwapHorizIcon from "@mui/icons-material/SwapHoriz";
import SubjectIcon from "@mui/icons-material/Subject";
import BugReportIcon from "@mui/icons-material/BugReport";
import type { EventType } from "../api/events";

const Icons: Record<EventType, typeof SwapHorizIcon> = {
  http: SwapHorizIcon,
  log: SubjectIcon,
  exception: BugReportIcon,
};

const baseColorsDark: Record<EventType, string> = {
  http: "#64b5f6",
  log: "#90a4ae",
  exception: "#ef9a9a",
};

const baseColorsLight: Record<EventType, string> = {
  http: "#1565c0",
  log: "#546e7a",
  exception: "#c62828",
};

const logLevelColorsDark: Record<string, string> = {
  DEBUG: "#90a4ae",
  INFO: "#90a4ae",
  WARNING: "#ffb74d",
  ERROR: "#ef9a9a",
  CRITICAL: "#ff8a80",
};

const logLevelColorsLight: Record<string, string> = {
  DEBUG: "#546e7a",
  INFO: "#546e7a",
  WARNING: "#e65100",
  ERROR: "#c62828",
  CRITICAL: "#b71c1c",
};

type Props = {
  eventType: EventType;
  dark?: boolean;
  level?: string;
  size?: number;
};

export default function EventTypeIcon({ eventType, dark = false, level, size = 18 }: Props) {
  const Icon = Icons[eventType];
  let color: string;
  if (eventType === "log" && level) {
    const palette = dark ? logLevelColorsDark : logLevelColorsLight;
    color = palette[level] ?? (dark ? baseColorsDark.log : baseColorsLight.log);
  } else {
    color = (dark ? baseColorsDark : baseColorsLight)[eventType];
  }
  return (
    <Icon
      sx={{
        color,
        fontSize: size,
        flexShrink: 0,
      }}
    />
  );
}
