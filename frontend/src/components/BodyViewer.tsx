import { useState, useMemo } from "react";
import JsonView from "react18-json-view";
import { Highlight, themes } from "prism-react-renderer";
import { XMLParser } from "fast-xml-parser";
import { customizeNode } from "../annotations";
import SseViewer, { parseSseEvents, type SseEvent } from "./SseViewer";
import LlmView from "../llm/LlmView";
import { detectLlmRequest, detectLlmResponse, detectLlmStreamResponse } from "../llm/detect";
import type { LlmView as LlmViewModel } from "../llm/types";
import "react18-json-view/src/style.css";
import Box from "@mui/material/Box";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import Typography from "@mui/material/Typography";

type ParsedBody =
  | { type: "json"; parsed: unknown; raw: string }
  | { type: "xml"; parsed: unknown; raw: string }
  | { type: "sse"; events: SseEvent[]; raw: string }
  | { type: "text"; raw: string }
  | { type: "llm-json"; view: LlmViewModel; parsed: unknown; raw: string }
  | { type: "llm-sse"; view: LlmViewModel; events: SseEvent[]; raw: string };

const preSx = {
  fontFamily: "monospace",
  fontSize: 13,
  whiteSpace: "pre-wrap",
  wordBreak: "break-all",
  m: 0,
} as const;

const xmlParser = new XMLParser({
  ignoreAttributes: false,
  attributeNamePrefix: "@_",
  removeNSPrefix: true,
  ignoreDeclaration: true,
  processEntities: false,
});

/** Remove @_xmlns attributes from the parsed tree (noise in the tree view). */
function stripXmlnsAttrs(obj: unknown): unknown {
  if (Array.isArray(obj)) return obj.map(stripXmlnsAttrs);
  if (typeof obj === "object" && obj !== null) {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(obj)) {
      if (k === "@_xmlns" || k.startsWith("@_xmlns:")) continue;
      out[k] = stripXmlnsAttrs(v);
    }
    return out;
  }
  return obj;
}

function parseBody(data: string): ParsedBody {
  // Try JSON first
  try {
    const parsed = JSON.parse(data);
    const view = detectLlmRequest(parsed) ?? detectLlmResponse(parsed);
    if (view) return { type: "llm-json", view, parsed, raw: data };
    return { type: "json", parsed, raw: data };
  } catch {
    // not JSON
  }

  // Try SSE
  const sseEvents = parseSseEvents(data);
  if (sseEvents) {
    const view = detectLlmStreamResponse(sseEvents);
    if (view) return { type: "llm-sse", view, events: sseEvents, raw: data };
    return { type: "sse", events: sseEvents, raw: data };
  }

  // Try XML
  const trimmed = data.trimStart();
  if (trimmed.startsWith("<")) {
    try {
      const parsed = xmlParser.parse(trimmed);
      // xmlParser.parse returns {} for invalid XML without throwing,
      // so check we got something meaningful
      if (parsed && Object.keys(parsed).length > 0) {
        return { type: "xml", parsed: stripXmlnsAttrs(parsed), raw: data };
      }
    } catch {
      // not valid XML
    }
  }

  return { type: "text", raw: data };
}

function prettyPrintXml(xml: string): string {
  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(xml.trim(), "text/xml");
    if (doc.querySelector("parsererror")) return xml;
    const serializer = new XMLSerializer();
    const raw = serializer.serializeToString(doc);
    // XMLSerializer doesn't indent — do it manually
    return formatXml(raw);
  } catch {
    return xml;
  }
}

function formatXml(xml: string): string {
  let indent = 0;
  const parts = xml.replace(/>\s*</g, ">\n<").split("\n");
  return parts
    .map((part) => {
      const trimmed = part.trim();
      if (!trimmed) return "";
      // Closing tag
      if (trimmed.startsWith("</")) indent = Math.max(0, indent - 1);
      const line = "  ".repeat(indent) + trimmed;
      // Opening tag (not self-closing, not closing)
      if (
        trimmed.startsWith("<") &&
        !trimmed.startsWith("</") &&
        !trimmed.startsWith("<?") &&
        !trimmed.endsWith("/>") &&
        // Don't indent tags with text content like <Name>foo</Name>
        !/<[^>]+>[^<]+<\//.test(trimmed)
      ) {
        indent++;
      }
      return line;
    })
    .join("\n");
}

function SyntaxHighlighted({ code, language }: { code: string; language: "json" | "xml" }) {
  return (
    <Highlight theme={themes.vsLight} code={code} language={language}>
      {({ tokens, getLineProps, getTokenProps }) => (
        <Typography component="pre" sx={{ ...preSx, background: "transparent !important" }}>
          {tokens.map((line, i) => (
            <div key={i} {...getLineProps({ line })}>
              {line.map((token, key) => (
                <span key={key} {...getTokenProps({ token })} />
              ))}
            </div>
          ))}
        </Typography>
      )}
    </Highlight>
  );
}

function TreeView({ parsed }: { parsed: unknown }) {
  return (
    <Box sx={{ fontSize: 13, fontFamily: "monospace" }}>
      <JsonView src={parsed} collapsed={2} customizeNode={customizeNode} />
    </Box>
  );
}

export default function BodyViewer({ data }: { data: string | null }) {
  const [tab, setTab] = useState(0);

  // Reset the selected tab when the body changes — different body types expose a
  // different number of tabs (LLM views have 3, JSON/XML/SSE have 2), so a carried-
  // over index can point past the last tab and render a blank panel.
  const [prevData, setPrevData] = useState(data);
  if (data !== prevData) {
    setPrevData(data);
    setTab(0);
  }

  const body = useMemo(() => (data ? parseBody(data) : null), [data]);

  if (!data || !body) return null;

  // Plain text — no tabs
  if (body.type === "text") {
    return (
      <Typography component="pre" sx={preSx}>
        {body.raw}
      </Typography>
    );
  }

  const tabsSx = {
    minHeight: 0,
    mb: 1,
    "& .MuiTab-root": { minHeight: 0, py: 0.5, px: 1.5, fontSize: 12 },
  } as const;

  // LLM (JSON request/response) — LLM / Tree / Raw tabs, LLM default
  if (body.type === "llm-json") {
    return (
      <Box>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={tabsSx}>
          <Tab label="LLM" />
          <Tab label="Tree" />
          <Tab label="Raw" />
        </Tabs>
        {tab === 0 && <LlmView view={body.view} />}
        {tab === 1 && <TreeView parsed={body.parsed} />}
        {tab === 2 && (
          <SyntaxHighlighted code={JSON.stringify(body.parsed, null, 2)} language="json" />
        )}
      </Box>
    );
  }

  // LLM (streaming SSE response) — LLM / Events / Raw tabs, LLM default
  if (body.type === "llm-sse") {
    return (
      <Box>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={tabsSx}>
          <Tab label="LLM" />
          <Tab label={`Events (${body.events.length})`} />
          <Tab label="Raw" />
        </Tabs>
        {tab === 0 && <LlmView view={body.view} />}
        {tab === 1 && <SseViewer events={body.events} />}
        {tab === 2 && (
          <Typography component="pre" sx={preSx}>
            {body.raw}
          </Typography>
        )}
      </Box>
    );
  }

  // SSE — Events / Raw tabs
  if (body.type === "sse") {
    return (
      <Box>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={tabsSx}>
          <Tab label={`Events (${body.events.length})`} />
          <Tab label="Raw" />
        </Tabs>
        {tab === 0 && <SseViewer events={body.events} />}
        {tab === 1 && (
          <Typography component="pre" sx={preSx}>
            {body.raw}
          </Typography>
        )}
      </Box>
    );
  }

  const rawCode =
    body.type === "json" ? JSON.stringify(body.parsed, null, 2) : prettyPrintXml(body.raw);

  return (
    <Box>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={tabsSx}>
        <Tab label="Tree" />
        <Tab label="Raw" />
      </Tabs>
      {tab === 0 && <TreeView parsed={body.parsed} />}
      {tab === 1 && <SyntaxHighlighted code={rawCode} language={body.type} />}
    </Box>
  );
}
