import Chip from "@mui/material/Chip";
import { mono } from "../theme";

const colorsLight: Record<string, string> = {
  DEBUG: "#78909c",
  INFO: "#1565c0",
  WARNING: "#e65100",
  ERROR: "#c62828",
  CRITICAL: "#b71c1c",
};

const colorsDark: Record<string, string> = {
  DEBUG: "#90a4ae",
  INFO: "#64b5f6",
  WARNING: "#ffb74d",
  ERROR: "#ef9a9a",
  CRITICAL: "#ff8a80",
};

type Props = {
  level: string;
  dark?: boolean;
};

export default function LogLevelBadge({ level, dark = false }: Props) {
  const colors = dark ? colorsDark : colorsLight;
  const color = colors[level] ?? (dark ? "#b0bec5" : "#78909c");

  return (
    <Chip
      label={level}
      size="small"
      variant="outlined"
      sx={{
        fontFamily: mono,
        fontWeight: 700,
        fontSize: 10,
        height: 20,
        minWidth: 36,
        color,
        borderColor: `${color}40`,
      }}
    />
  );
}
