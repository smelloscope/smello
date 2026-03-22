import Chip from "@mui/material/Chip";
import { mono } from "../theme";

const methodColorsLight: Record<string, string> = {
  GET: "#1565c0",
  POST: "#2e7d32",
  PUT: "#e65100",
  PATCH: "#7b1fa2",
  DELETE: "#c62828",
  HEAD: "#546e7a",
  OPTIONS: "#546e7a",
};

const methodColorsDark: Record<string, string> = {
  GET: "#64b5f6",
  POST: "#81c784",
  PUT: "#ffb74d",
  PATCH: "#ce93d8",
  DELETE: "#ef9a9a",
  HEAD: "#90a4ae",
  OPTIONS: "#90a4ae",
};

type MethodBadgeProps = {
  method: string;
  size?: "small" | "medium";
  dark?: boolean;
};

export default function MethodBadge({ method, size = "small", dark = false }: MethodBadgeProps) {
  const colors = dark ? methodColorsDark : methodColorsLight;
  const color = colors[method] ?? (dark ? "#b0bec5" : "#78909c");

  return (
    <Chip
      label={method}
      size="small"
      variant="outlined"
      sx={{
        fontFamily: mono,
        fontWeight: 700,
        fontSize: size === "medium" ? 12 : 11,
        height: size === "medium" ? 24 : 20,
        color,
        borderColor: `${color}40`,
      }}
    />
  );
}
