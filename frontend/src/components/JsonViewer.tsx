import JsonView from "react18-json-view";
import "react18-json-view/src/style.css";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

function tryParseJson(data: string): unknown | undefined {
  try {
    return JSON.parse(data);
  } catch {
    return undefined;
  }
}

export default function JsonViewer({ data }: { data: string | null }) {
  if (!data) return null;

  const parsed = tryParseJson(data);

  if (parsed !== undefined) {
    return (
      <Box sx={{ fontSize: 13, fontFamily: "monospace" }}>
        <JsonView src={parsed} collapsed={2} />
      </Box>
    );
  }

  return (
    <Typography
      component="pre"
      sx={{
        fontFamily: "monospace",
        fontSize: 13,
        whiteSpace: "pre-wrap",
        wordBreak: "break-all",
        m: 0,
      }}
    >
      {data}
    </Typography>
  );
}
