/** Small type guards / coercions shared by the provider adapters. */

export function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

export function asString(v: unknown): string {
  return typeof v === "string" ? v : "";
}

export function numOrUndef(v: unknown): number | undefined {
  return typeof v === "number" && Number.isFinite(v) ? v : undefined;
}

/** Parse JSON, returning `null` on failure. (`null` also results from the literal `null`.) */
export function tryParseJson(s: string): unknown {
  try {
    return JSON.parse(s);
  } catch {
    return null;
  }
}
