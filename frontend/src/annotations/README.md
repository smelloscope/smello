# JSON Value Annotations

The annotation system recognizes patterns in JSON response bodies — currently Unix timestamps — and shows a tooltip with the human-readable value.

## How it works

`react18-json-view` calls our `customizeNode` callback for every node in the JSON tree. For each leaf value (skipping objects and arrays), we pass it through a list of **annotators** — functions that examine a value and return an **annotation** or `undefined`. The first match wins. When an annotator matches, the value renders with a small icon whose tooltip shows the interpretation.

```
customizeNode (per JSON node)
  → runAnnotators(annotators, value, key)
    → detectUnixSeconds(value, key)   → TimestampAnnotation | undefined
    → detectUnixMs(value, key)        → TimestampAnnotation | undefined
    → ...future annotators
  → AnnotatedValue component
    → annotation.render()             → tooltip content
```

## File structure

```
annotations/
├── types.ts              # Annotation interface, Annotator type, runAnnotators()
├── timestamp.ts          # TimestampAnnotation + detectUnixSeconds/detectUnixMs
├── registry.ts           # defaultAnnotators array — the single registration point
├── AnnotatedValue.tsx    # Renders value + MUI Tooltip with icon
├── customizeNode.tsx     # Callback passed to react18-json-view
├── index.ts              # Public export (just customizeNode)
└── __tests__/
    ├── timestamp.test.ts
    ├── AnnotatedValue.test.tsx
    └── customizeNode.test.tsx
```

## Adding a new annotator

Adding a UUID annotator as an example:

### 1. Create the annotator file

```typescript
// annotations/uuid.ts
import type { Annotation, Annotator } from "./types";

class UuidAnnotation implements Annotation {
  readonly kind = "uuid";
  constructor(readonly version: number) {}

  render() {
    return `UUID v${this.version}`;
  }
}

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-([1-5])[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export const detectUuid: Annotator = (value) => {
  if (typeof value !== "string") return undefined;
  const match = UUID_RE.exec(value);
  if (!match) return undefined;
  return new UuidAnnotation(Number(match[1]));
};
```

### 2. Register it

```typescript
// registry.ts
import { detectUnixSeconds, detectUnixMs } from "./timestamp";
import { detectUuid } from "./uuid";

export const defaultAnnotators: Annotator[] = [
  detectUnixSeconds,
  detectUnixMs,
  detectUuid, // ← add here
];
```

### 3. Add tests

Create `__tests__/uuid.test.ts` with tests for the detector function. Detection logic is pure functions — tests run without jsdom.

Two files, done. The rest of the system (`types.ts`, `AnnotatedValue.tsx`, `customizeNode.tsx`, `index.ts`, `JsonViewer.tsx`) stays untouched.

## Design notes

- **`customizeNode` lives at module scope**, not inside a component, so its reference stays stable across renders.
- **`AnnotatedValue` uses `<span>` elements**, not `<div>`, to remain inline within the library's `.json-view--pair` layout.
- **CSS classes** (`json-view--number`, `json-view--string`, etc.) match the library's own rendering, so annotated values look identical to unannotated ones.
- **Annotator functions are stateless.** They receive a value and return an annotation or `undefined`. All state lives in the `Annotation` object.
- **Timestamp ranges** span year 2000–2100: `[946684800, 4102444800)` for seconds, `[946684800000, 4102444800000)` for milliseconds. The ranges are disjoint, so order between the two detectors is irrelevant. `Number.isInteger` rejects floats to prevent false positives.

## Running tests

```bash
cd frontend && npm test
```

All annotation tests run as pure logic or lightweight React Testing Library renders — everything runs in jsdom.
