import Tooltip from "@mui/material/Tooltip";
import HelpOutline from "@mui/icons-material/HelpOutline";
import type { Annotation } from "./types";

function cssClass(value: unknown): string {
  switch (typeof value) {
    case "number":
    case "bigint":
      return "json-view--number";
    case "boolean":
      return "json-view--boolean";
    case "string":
      return "json-view--string";
    default:
      return "json-view--null";
  }
}

function formatValue(value: unknown): string {
  if (typeof value === "string") return `"${value}"`;
  return String(value);
}

export default function AnnotatedValue({
  value,
  annotation,
}: {
  value: unknown;
  annotation: Annotation;
}) {
  return (
    <span>
      <span className={cssClass(value)}>{formatValue(value)}</span>
      <Tooltip title={annotation.render()} arrow>
        <HelpOutline
          sx={{
            fontSize: 12,
            ml: 0.5,
            verticalAlign: "middle",
            color: "text.disabled",
            cursor: "default",
          }}
        />
      </Tooltip>
    </span>
  );
}
