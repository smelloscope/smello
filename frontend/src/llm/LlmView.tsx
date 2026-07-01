import JsonView from "react18-json-view";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Chip from "@mui/material/Chip";
import Paper from "@mui/material/Paper";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { customizeNode } from "../annotations";
import { mono } from "../theme";
import type { LlmBlock, LlmMessage, LlmRole, LlmView as LlmViewModel } from "./types";

const roleStyles: Record<LlmRole, { label: string; color: string; bg: string }> = {
  system: { label: "System", color: "#6d4c41", bg: "rgba(109,76,65,0.05)" },
  user: { label: "User", color: "#1976d2", bg: "rgba(25,118,210,0.05)" },
  assistant: { label: "Assistant", color: "#2e7d32", bg: "rgba(46,125,50,0.05)" },
  tool: { label: "Tool", color: "#7b1fa2", bg: "rgba(123,31,162,0.05)" },
};

const textSx = {
  fontSize: 13,
  whiteSpace: "pre-wrap",
  wordBreak: "break-word",
  m: 0,
} as const;

function TokenLine({ usage }: { usage: NonNullable<LlmViewModel["usage"]> }) {
  const parts: string[] = [];
  if (usage.inputTokens !== undefined) parts.push(`${usage.inputTokens} in`);
  if (usage.outputTokens !== undefined) parts.push(`${usage.outputTokens} out`);
  if (usage.cacheReadTokens) parts.push(`${usage.cacheReadTokens} cache read`);
  if (usage.cacheWriteTokens) parts.push(`${usage.cacheWriteTokens} cache write`);
  if (!parts.length) return null;
  return (
    <Typography sx={{ fontFamily: mono, fontSize: 12, color: "text.secondary" }}>
      {parts.join(" · ")}
    </Typography>
  );
}

function JsonBox({ src }: { src: unknown }) {
  if (typeof src === "string") {
    return (
      <Typography component="pre" sx={{ ...textSx, fontFamily: mono, color: "text.primary" }}>
        {src}
      </Typography>
    );
  }
  return (
    <Box sx={{ fontSize: 12, fontFamily: mono }}>
      <JsonView src={src} collapsed={1} customizeNode={customizeNode} />
    </Box>
  );
}

function BlockView({ block }: { block: LlmBlock }) {
  switch (block.kind) {
    case "text":
      return (
        <Typography component="pre" sx={textSx}>
          {block.text}
        </Typography>
      );
    case "thinking":
      return (
        <Typography
          component="pre"
          sx={{ ...textSx, fontStyle: "italic", color: "text.secondary" }}
        >
          {block.text}
        </Typography>
      );
    case "image":
      return (
        <Chip
          label={block.media ? `image (${block.media})` : "image"}
          size="small"
          variant="outlined"
          sx={{ fontSize: 11, height: 22, color: "text.secondary", borderColor: "divider" }}
        />
      );
    case "tool_use":
      return (
        <Paper
          variant="outlined"
          sx={{ p: 1, bgcolor: "rgba(123,31,162,0.04)", borderColor: "rgba(123,31,162,0.2)" }}
        >
          <Stack direction="row" spacing={0.5} alignItems="baseline" sx={{ mb: 0.5 }}>
            <Typography sx={{ fontSize: 11, fontWeight: 700, color: "#7b1fa2" }}>
              → {block.name || "tool"}
            </Typography>
            {block.id && (
              <Typography sx={{ fontFamily: mono, fontSize: 11, color: "text.disabled" }}>
                {block.id}
              </Typography>
            )}
          </Stack>
          <JsonBox src={block.input} />
        </Paper>
      );
    case "tool_result": {
      const color = block.isError ? "#d32f2f" : "#2e7d32";
      return (
        <Paper
          variant="outlined"
          sx={{
            p: 1,
            bgcolor: block.isError ? "rgba(211,47,47,0.04)" : "rgba(46,125,50,0.04)",
            borderColor: block.isError ? "rgba(211,47,47,0.2)" : "rgba(46,125,50,0.2)",
          }}
        >
          <Typography sx={{ fontSize: 11, fontWeight: 700, color, mb: 0.5 }}>
            ← tool result{block.isError ? " (error)" : ""}
          </Typography>
          <JsonBox src={block.content} />
        </Paper>
      );
    }
    case "unknown":
      return <JsonBox src={block.raw} />;
    default: {
      // Compile-time exhaustiveness: adding a new LlmBlock kind without a case here
      // becomes a type error instead of silently rendering nothing.
      const _exhaustive: never = block;
      void _exhaustive;
      return null;
    }
  }
}

function MessageView({ message }: { message: LlmMessage }) {
  const style = roleStyles[message.role];
  return (
    <Box
      sx={{
        borderLeft: "3px solid",
        borderColor: style.color,
        bgcolor: style.bg,
        borderRadius: "0 4px 4px 0",
        px: 1.5,
        py: 1,
      }}
    >
      <Typography
        sx={{
          fontSize: 11,
          fontWeight: 700,
          color: style.color,
          textTransform: "uppercase",
          mb: 0.5,
        }}
      >
        {style.label}
      </Typography>
      <Stack spacing={0.75}>
        {message.blocks.length ? (
          message.blocks.map((b, i) => <BlockView key={i} block={b} />)
        ) : (
          <Typography sx={{ fontSize: 12, color: "text.disabled", fontStyle: "italic" }}>
            (empty)
          </Typography>
        )}
      </Stack>
    </Box>
  );
}

export default function LlmView({ view }: { view: LlmViewModel }) {
  const systemBlocks = view.system ?? [];
  return (
    <Stack spacing={1.25}>
      <Stack direction="row" spacing={0.75} alignItems="center" sx={{ flexWrap: "wrap" }}>
        {view.model && (
          <Chip
            label={view.model}
            size="small"
            sx={{
              fontFamily: mono,
              fontSize: 11,
              height: 22,
              fontWeight: 600,
              bgcolor: "#FFA600",
              color: "#2A2A2E",
            }}
          />
        )}
        <Chip
          label={view.provider}
          size="small"
          variant="outlined"
          sx={{ fontSize: 11, height: 22, color: "text.secondary", borderColor: "divider" }}
        />
        {view.stopReason && (
          <Chip
            label={view.stopReason}
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
        {view.usage && <TokenLine usage={view.usage} />}
      </Stack>

      {systemBlocks.length > 0 && (
        <MessageView message={{ role: "system", blocks: systemBlocks }} />
      )}

      {view.tools && view.tools.length > 0 && (
        <Stack direction="row" spacing={0.5} alignItems="center" sx={{ flexWrap: "wrap" }}>
          <Typography sx={{ fontSize: 11, fontWeight: 700, color: "text.secondary", mr: 0.5 }}>
            Tools ({view.tools.length}):
          </Typography>
          {view.tools.map((t, i) => (
            <Tooltip
              key={i}
              title={t.description ?? ""}
              arrow
              disableHoverListener={!t.description}
            >
              <Chip
                label={t.name}
                size="small"
                variant="outlined"
                sx={{
                  fontFamily: mono,
                  fontSize: 11,
                  height: 20,
                  color: "text.secondary",
                  borderColor: "divider",
                }}
              />
            </Tooltip>
          ))}
        </Stack>
      )}

      {view.messages.map((m, i) => (
        <MessageView key={i} message={m} />
      ))}
    </Stack>
  );
}
