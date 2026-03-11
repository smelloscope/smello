import { describe, expect, it, vi } from "vitest";
import { detectUnixSeconds, detectUnixMs, TimestampAnnotation } from "../timestamp";
import { runAnnotators } from "../types";
import type { Annotator } from "../types";

describe("detectUnixSeconds", () => {
  it("detects a valid unix timestamp in seconds", () => {
    const result = detectUnixSeconds(1705312245, undefined);
    expect(result).toBeInstanceOf(TimestampAnnotation);
    expect(result!.kind).toBe("unix-seconds");
    expect((result as TimestampAnnotation).date.getUTCFullYear()).toBe(2024);
  });

  it("rejects too-small numbers", () => {
    expect(detectUnixSeconds(123, undefined)).toBeUndefined();
  });

  it("rejects millisecond-range numbers", () => {
    expect(detectUnixSeconds(1705312245123, undefined)).toBeUndefined();
  });

  it("rejects strings", () => {
    expect(detectUnixSeconds("1705312245", undefined)).toBeUndefined();
  });

  it("rejects floats", () => {
    expect(detectUnixSeconds(1705312245.5, undefined)).toBeUndefined();
  });

  it("rejects null", () => {
    expect(detectUnixSeconds(null, undefined)).toBeUndefined();
  });

  it("rejects booleans", () => {
    expect(detectUnixSeconds(true, undefined)).toBeUndefined();
  });

  it("rejects objects", () => {
    expect(detectUnixSeconds({}, undefined)).toBeUndefined();
  });

  it("rejects arrays", () => {
    expect(detectUnixSeconds([], undefined)).toBeUndefined();
  });
});

describe("detectUnixMs", () => {
  it("detects a valid unix timestamp in milliseconds", () => {
    const result = detectUnixMs(1705312245123, undefined);
    expect(result).toBeInstanceOf(TimestampAnnotation);
    expect(result!.kind).toBe("unix-ms");
    expect((result as TimestampAnnotation).date.getUTCFullYear()).toBe(2024);
  });

  it("rejects seconds-range numbers", () => {
    expect(detectUnixMs(1705312245, undefined)).toBeUndefined();
  });
});

describe("TimestampAnnotation.render", () => {
  it("formats a UTC date string", () => {
    const ann = new TimestampAnnotation(1705312245, "unix-seconds");
    expect(ann.render()).toBe("2024-01-15 09:50:45 UTC");
  });
});

describe("runAnnotators", () => {
  it("returns the first match and skips later annotators", () => {
    const first: Annotator = () => new TimestampAnnotation(1705312245, "unix-seconds");
    const second: Annotator = vi.fn(() => undefined);

    const result = runAnnotators([first, second], 1705312245, undefined);
    expect(result).toBeInstanceOf(TimestampAnnotation);
    expect(second).not.toHaveBeenCalled();
  });

  it("returns undefined when nothing matches", () => {
    const a: Annotator = () => undefined;
    expect(runAnnotators([a], "hello", undefined)).toBeUndefined();
  });
});
