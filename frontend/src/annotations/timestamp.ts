import type { ReactNode } from "react";
import type { Annotation, Annotator } from "./types";

// Year 2000–2100 in seconds
const MIN_SECONDS = 946684800;
const MAX_SECONDS = 4102444800;

// Same range in milliseconds
const MIN_MS = MIN_SECONDS * 1000;
const MAX_MS = MAX_SECONDS * 1000;

export class TimestampAnnotation implements Annotation {
  readonly kind: string;
  readonly date: Date;
  readonly format: "unix-seconds" | "unix-ms";

  constructor(value: number, format: "unix-seconds" | "unix-ms") {
    this.kind = format;
    this.format = format;
    this.date = format === "unix-seconds" ? new Date(value * 1000) : new Date(value);
  }

  render(): ReactNode {
    return this.date.toISOString().replace("T", " ").replace(".000Z", " UTC");
  }
}

export const detectUnixSeconds: Annotator = (value) => {
  if (typeof value !== "number" || !Number.isInteger(value)) return undefined;
  if (value < MIN_SECONDS || value >= MAX_SECONDS) return undefined;
  return new TimestampAnnotation(value, "unix-seconds");
};

export const detectUnixMs: Annotator = (value) => {
  if (typeof value !== "number" || !Number.isInteger(value)) return undefined;
  if (value < MIN_MS || value >= MAX_MS) return undefined;
  return new TimestampAnnotation(value, "unix-ms");
};
