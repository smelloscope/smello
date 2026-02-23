import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableRow from "@mui/material/TableRow";

export default function HeadersTable({ headers }: { headers: Record<string, string> }) {
  const entries = Object.entries(headers);
  if (entries.length === 0) return null;

  return (
    <Table size="small">
      <TableBody>
        {entries.map(([key, value]) => (
          <TableRow key={key}>
            <TableCell sx={{ fontWeight: 600, whiteSpace: "nowrap", width: "1%" }}>{key}</TableCell>
            <TableCell sx={{ fontFamily: "monospace", wordBreak: "break-all" }}>{value}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
