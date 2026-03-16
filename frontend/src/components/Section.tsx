import { useState } from "react";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Paper from "@mui/material/Paper";
import Collapse from "@mui/material/Collapse";
import ButtonBase from "@mui/material/ButtonBase";
import ExpandMore from "@mui/icons-material/ExpandMore";
import CallMade from "@mui/icons-material/CallMade";
import CallReceived from "@mui/icons-material/CallReceived";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableRow from "@mui/material/TableRow";
import HeadersTable from "./HeadersTable";
import BodyViewer from "./BodyViewer";
import CopyButton from "./CopyButton";

type SectionProps = {
  title: string;
  headers: Record<string, string>;
  body: string | null;
  bodySize: number;
  queryParams?: [string, string][];
};

const chevronSx = (open: boolean) => ({
  color: "text.secondary",
  transform: open ? "rotate(180deg)" : "rotate(0deg)",
  transition: "transform 150ms",
});

export default function Section({ title, headers, body, bodySize, queryParams }: SectionProps) {
  const [queryParamsOpen, setQueryParamsOpen] = useState(false);
  const [headersOpen, setHeadersOpen] = useState(false);
  const [bodyOpen, setBodyOpen] = useState(true);
  const headerCount = Object.keys(headers).length;
  const hasQueryParams = queryParams && queryParams.length > 0;
  const isRequest = title === "Request";
  const Icon = isRequest ? CallMade : CallReceived;

  return (
    <Box sx={{ mb: 2 }}>
      <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mb: 0.5 }}>
        <Icon
          sx={{
            fontSize: 16,
            color: isRequest ? "primary.main" : "success.main",
          }}
        />
        <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
          {title}
        </Typography>
      </Stack>
      {hasQueryParams && (
        <Paper variant="outlined" sx={{ mb: 1 }}>
          <ButtonBase
            disableRipple
            onClick={() => setQueryParamsOpen((o) => !o)}
            sx={{
              width: "100%",
              justifyContent: "space-between",
              p: 1,
              textAlign: "left",
            }}
          >
            <Typography variant="caption" sx={{ fontWeight: 600, color: "text.secondary" }}>
              Query Parameters ({queryParams.length})
            </Typography>
            <ExpandMore fontSize="small" sx={chevronSx(queryParamsOpen)} />
          </ButtonBase>
          <Collapse in={queryParamsOpen}>
            <Box sx={{ px: 1, pb: 1 }}>
              <Table size="small">
                <TableBody>
                  {queryParams.map(([key, value], i) => (
                    <TableRow key={`${key}-${i}`}>
                      <TableCell sx={{ fontWeight: 600, whiteSpace: "nowrap", width: "1%" }}>
                        {key}
                      </TableCell>
                      <TableCell sx={{ fontFamily: "monospace", wordBreak: "break-all" }}>
                        {value}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          </Collapse>
        </Paper>
      )}
      <Paper variant="outlined" sx={{ mb: 1 }}>
        <ButtonBase
          disableRipple
          onClick={() => setHeadersOpen((o) => !o)}
          sx={{
            width: "100%",
            justifyContent: "space-between",
            p: 1,
            textAlign: "left",
          }}
        >
          <Typography variant="caption" sx={{ fontWeight: 600, color: "text.secondary" }}>
            Headers ({headerCount})
          </Typography>
          <ExpandMore fontSize="small" sx={chevronSx(headersOpen)} />
        </ButtonBase>
        <Collapse in={headersOpen}>
          <Box sx={{ px: 1, pb: 1 }}>
            <HeadersTable headers={headers} />
          </Box>
        </Collapse>
      </Paper>
      {body && (
        <Paper variant="outlined">
          <Stack direction="row" alignItems="center" sx={{ p: 1 }}>
            <ButtonBase
              disableRipple
              onClick={() => setBodyOpen((o) => !o)}
              sx={{ flex: 1, justifyContent: "space-between", textAlign: "left" }}
            >
              <Typography variant="caption" sx={{ fontWeight: 600, color: "text.secondary" }}>
                Body ({bodySize} bytes)
              </Typography>
              <ExpandMore fontSize="small" sx={chevronSx(bodyOpen)} />
            </ButtonBase>
            <CopyButton text={body} />
          </Stack>
          <Collapse in={bodyOpen}>
            <Box sx={{ px: 1, pb: 1 }}>
              <BodyViewer data={body} />
            </Box>
          </Collapse>
        </Paper>
      )}
    </Box>
  );
}
