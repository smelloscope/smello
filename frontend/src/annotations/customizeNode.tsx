import type { ReactElement } from "react";
import { runAnnotators } from "./types";
import { defaultAnnotators } from "./registry";
import AnnotatedValue from "./AnnotatedValue";

export function customizeNode({
  node,
  indexOrName,
}: {
  node: unknown;
  indexOrName?: string | number;
  depth: number;
}): ReactElement | undefined {
  if (typeof node === "object" && node !== null) return undefined;

  const annotation = runAnnotators(defaultAnnotators, node, indexOrName);
  if (!annotation) return undefined;

  return <AnnotatedValue value={node} annotation={annotation} />;
}
