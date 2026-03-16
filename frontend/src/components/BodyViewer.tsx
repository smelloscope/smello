import { useState, useMemo } from "react";
import JsonView from "react18-json-view";
import { Highlight, themes } from "prism-react-renderer";
import { XMLParser } from "fast-xml-parser";
import { customizeNode } from "../annotations";
import "react18-json-view/src/style.css";
import Box from "@mui/material/Box";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import Typography from "@mui/material/Typography";

type ParsedBody =
  | { type: "json"; parsed: unknown; raw: string }
  | { type: "xml"; parsed: unknown; raw: string }
  | { type: "text"; raw: string };

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
    return { type: "json", parsed: JSON.parse(data), raw: data };
  } catch {
    // not JSON
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

  const rawCode =
    body.type === "json" ? JSON.stringify(body.parsed, null, 2) : prettyPrintXml(body.raw);

  return (
    <Box>
      <Tabs
        value={tab}
        onChange={(_, v) => setTab(v)}
        sx={{
          minHeight: 0,
          mb: 1,
          "& .MuiTab-root": { minHeight: 0, py: 0.5, px: 1.5, fontSize: 12 },
        }}
      >
        <Tab label="Tree" />
        <Tab label="Raw" />
      </Tabs>
      {tab === 0 && <TreeView parsed={body.parsed} />}
      {tab === 1 && <SyntaxHighlighted code={rawCode} language={body.type} />}
    </Box>
  );
}
