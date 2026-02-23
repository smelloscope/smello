import Chip from "@mui/material/Chip";

type ChipColor = "success" | "info" | "warning" | "error";

function getChipColor(status: number): ChipColor {
  if (status >= 500) return "error";
  if (status >= 400) return "warning";
  if (status >= 300) return "info";
  return "success";
}

export default function StatusBadge({ status }: { status: number }) {
  return (
    <Chip
      label={status}
      size="small"
      color={getChipColor(status)}
      sx={{
        fontWeight: 600,
        fontSize: 12,
        height: 22,
        minWidth: 40,
      }}
    />
  );
}
