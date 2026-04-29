import { useState } from "react";
import Box from "@mui/material/Box";
import Collapse from "@mui/material/Collapse";
import IconButton from "@mui/material/IconButton";
import Stack from "@mui/material/Stack";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import Paper from "@mui/material/Paper";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import { Highlight, themes } from "prism-react-renderer";
import CopyButton from "../CopyButton";
import type { EventDetail, ExceptionEventData } from "../../api/events";

const mono = "'SF Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace";

type Frame = ExceptionEventData["frames"][number];

function vscodeUrl(path: string, line: number): string {
  return `vscode://file/${encodeURI(path)}:${line}`;
}

function shortenPath(path: string, segments = 3): string {
  const parts = path.split("/").filter(Boolean);
  if (parts.length <= segments) return path;
  return "…/" + parts.slice(-segments).join("/");
}

function hasSnippet(frame: Frame): boolean {
  return (frame.pre_context?.length ?? 0) > 0 || (frame.post_context?.length ?? 0) > 0;
}

function FrameSnippet({ frame }: { frame: Frame }) {
  const pre = frame.pre_context ?? [];
  const post = frame.post_context ?? [];
  const errorLine = frame.context_line ?? "";

  const startLineno = frame.lineno - pre.length;
  const allLines = [...pre, errorLine, ...post];
  const errorIdx = pre.length;
  const code = allLines.join("\n");

  return (
    <Box
      sx={{
        bgcolor: "rgba(0,0,0,0.02)",
        borderTop: "1px solid",
        borderColor: "divider",
        overflow: "auto",
      }}
    >
      <Highlight theme={themes.vsLight} code={code} language="python">
        {({ tokens, getLineProps, getTokenProps }) => (
          <Box
            component="pre"
            sx={{
              fontFamily: mono,
              fontSize: 12,
              m: 0,
              p: 0,
              lineHeight: 1.55,
              background: "transparent !important",
            }}
          >
            {tokens.map((line, i) => {
              const isError = i === errorIdx;
              return (
                <Box
                  key={i}
                  {...getLineProps({ line })}
                  sx={{
                    display: "flex",
                    bgcolor: isError ? "rgba(239,154,154,0.18)" : undefined,
                    borderLeft: isError ? "3px solid #ef5350" : "3px solid transparent",
                    px: 1,
                  }}
                >
                  <Box
                    component="span"
                    sx={{
                      display: "inline-block",
                      minWidth: 36,
                      textAlign: "right",
                      pr: 1.5,
                      color: "text.disabled",
                      userSelect: "none",
                      flexShrink: 0,
                    }}
                  >
                    {startLineno + i}
                  </Box>
                  <Box component="span" sx={{ whiteSpace: "pre" }}>
                    {line.map((token, key) => (
                      <span key={key} {...getTokenProps({ token })} />
                    ))}
                  </Box>
                </Box>
              );
            })}
          </Box>
        )}
      </Highlight>
    </Box>
  );
}

function FrameItem({ frame, isLast }: { frame: Frame; isLast: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const expandable = hasSnippet(frame);
  const sourceLine = frame.context_line?.trim() ?? "";

  return (
    <Box
      sx={{
        borderBottom: isLast ? 0 : "1px solid",
        borderColor: "divider",
      }}
    >
      <Box
        onClick={() => expandable && setExpanded((v) => !v)}
        sx={{
          display: "flex",
          alignItems: "flex-start",
          gap: 1,
          px: 1.5,
          py: 1,
          cursor: expandable ? "pointer" : "default",
          "&:hover": expandable ? { bgcolor: "action.hover" } : undefined,
        }}
      >
        {expandable ? (
          <IconButton
            size="small"
            sx={{ p: 0.25, mt: -0.25 }}
            onClick={(e) => {
              e.stopPropagation();
              setExpanded((v) => !v);
            }}
            aria-label={expanded ? "collapse snippet" : "expand snippet"}
          >
            {expanded ? (
              <KeyboardArrowDownIcon fontSize="inherit" />
            ) : (
              <KeyboardArrowRightIcon fontSize="inherit" />
            )}
          </IconButton>
        ) : (
          <Box sx={{ width: 22, flexShrink: 0 }} />
        )}
        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
          <Stack direction="row" alignItems="center" spacing={1} sx={{ flexWrap: "wrap" }}>
            <Tooltip title={frame.filename} placement="top-start" enterDelay={400}>
              <Typography
                sx={{
                  fontFamily: mono,
                  fontSize: 12,
                  color: "text.secondary",
                }}
              >
                {shortenPath(frame.filename)}:{frame.lineno}
              </Typography>
            </Tooltip>
            <Typography
              sx={{
                fontFamily: mono,
                fontSize: 12,
                color: "text.disabled",
              }}
            >
              in
            </Typography>
            <Typography
              sx={{
                fontFamily: mono,
                fontSize: 12,
                color: "text.primary",
              }}
            >
              {frame.function}
            </Typography>
          </Stack>
          {sourceLine && (
            <Typography
              sx={{
                fontFamily: mono,
                fontSize: 12,
                color: "text.secondary",
                mt: 0.25,
                wordBreak: "break-all",
              }}
            >
              {sourceLine}
            </Typography>
          )}
        </Box>
        <Tooltip title="Open in VS Code">
          <Box
            component="a"
            href={vscodeUrl(frame.filename, frame.lineno)}
            onClick={(e) => e.stopPropagation()}
            sx={{
              display: "inline-flex",
              alignItems: "center",
              alignSelf: "center",
              ml: 1,
              opacity: 0.5,
              transition: "opacity 0.15s",
              "&:hover": { opacity: 1 },
            }}
          >
            <Box
              component="img"
              src="/icon-vscode.svg"
              alt=""
              sx={{ width: 14, height: 14, display: "block" }}
            />
          </Box>
        </Tooltip>
      </Box>
      {expandable && (
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <FrameSnippet frame={frame} />
        </Collapse>
      )}
    </Box>
  );
}

export default function ExceptionDetail({ detail }: { detail: EventDetail }) {
  const d = detail.data as unknown as ExceptionEventData;

  return (
    <Box sx={{ p: 2, overflowY: "auto" }}>
      <Box sx={{ mb: 2 }}>
        <Stack direction="row" alignItems="baseline" spacing={1} sx={{ mb: 0.5 }}>
          <Chip
            label="EXCEPTION"
            size="small"
            sx={{
              fontFamily: mono,
              fontWeight: 700,
              fontSize: 10,
              height: 20,
              color: "#ef9a9a",
              bgcolor: "rgba(239,154,154,0.15)",
              borderRadius: 1,
            }}
          />
          <Typography
            sx={{
              fontFamily: mono,
              fontSize: 16,
              fontWeight: 700,
              color: "error.main",
            }}
          >
            {d.exc_type}
          </Typography>
        </Stack>

        <Typography
          sx={{
            fontSize: 14,
            mb: 1.5,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {d.exc_value}
        </Typography>

        <Stack direction="row" alignItems="center" spacing={1}>
          {d.exc_module && (
            <Chip
              label={d.exc_module}
              size="small"
              variant="outlined"
              sx={{
                fontFamily: mono,
                fontSize: 11,
                height: 22,
                color: "text.secondary",
                borderColor: "divider",
              }}
            />
          )}
          <Typography variant="body2" color="text.disabled" sx={{ fontSize: 12 }}>
            {new Date(detail.timestamp).toLocaleString()}
          </Typography>
        </Stack>
      </Box>

      <Divider sx={{ mb: 2 }} />

      {/* Traceback */}
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 0.5 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
          Traceback
        </Typography>
        <CopyButton text={d.traceback_text} />
      </Stack>
      <Paper
        variant="outlined"
        sx={{
          p: 1.5,
          mb: 2,
          bgcolor: "rgba(239,154,154,0.04)",
          borderColor: "rgba(239,154,154,0.2)",
          overflow: "auto",
        }}
      >
        <Highlight theme={themes.vsLight} code={d.traceback_text} language="python">
          {({ tokens, getLineProps, getTokenProps }) => (
            <Box
              component="pre"
              sx={{
                fontFamily: mono,
                fontSize: 12,
                m: 0,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                lineHeight: 1.6,
                background: "transparent !important",
              }}
            >
              {tokens.map((line, i) => (
                <Box key={i} {...getLineProps({ line })}>
                  {line.map((token, key) => (
                    <span key={key} {...getTokenProps({ token })} />
                  ))}
                </Box>
              ))}
            </Box>
          )}
        </Highlight>
      </Paper>

      {/* Frames */}
      {d.frames && d.frames.length > 0 && (
        <>
          <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 0.5 }}>
            Frames ({d.frames.length})
          </Typography>
          <Paper variant="outlined" sx={{ mb: 2 }}>
            {d.frames.map((frame, i) => (
              <FrameItem key={i} frame={frame} isLast={i === d.frames.length - 1} />
            ))}
          </Paper>
        </>
      )}
    </Box>
  );
}
