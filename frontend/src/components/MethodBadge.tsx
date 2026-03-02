import Typography from "@mui/material/Typography";

const methodColors: Record<string, string> = {
  GET: "#1565c0",
  POST: "#2e7d32",
  PUT: "#e65100",
  PATCH: "#7b1fa2",
  DELETE: "#c62828",
  HEAD: "#546e7a",
  OPTIONS: "#546e7a",
};

type MethodBadgeProps = {
  method: string;
  size?: "small" | "medium";
};

export default function MethodBadge({ method, size = "small" }: MethodBadgeProps) {
  const color = methodColors[method] ?? "#78909c";
  const fontSize = size === "medium" ? 13 : 11;
  const px = size === "medium" ? 1 : 0.75;
  const py = size === "medium" ? 0.25 : 0;

  return (
    <Typography
      component="span"
      sx={{
        fontFamily: "'SF Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace",
        fontWeight: 700,
        fontSize,
        color,
        bgcolor: `${color}14`,
        px,
        py,
        borderRadius: 0.5,
        lineHeight: 1.5,
        letterSpacing: 0.3,
      }}
    >
      {method}
    </Typography>
  );
}
