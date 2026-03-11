import type { ReactNode } from "react";

export interface Annotation {
  readonly kind: string;
  render(): ReactNode;
}

export type Annotator = (
  value: unknown,
  key: string | number | undefined,
) => Annotation | undefined;

export function runAnnotators(
  annotators: Annotator[],
  value: unknown,
  key: string | number | undefined,
): Annotation | undefined {
  for (const annotator of annotators) {
    const result = annotator(value, key);
    if (result !== undefined) return result;
  }
  return undefined;
}
