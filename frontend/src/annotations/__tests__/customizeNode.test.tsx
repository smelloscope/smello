import { describe, expect, it } from "vitest";
import { isValidElement } from "react";
import { customizeNode } from "../customizeNode";

describe("customizeNode", () => {
  it("returns a ReactElement for a timestamp value", () => {
    const result = customizeNode({
      node: 1705312245,
      indexOrName: "created_at",
      depth: 1,
    });
    expect(isValidElement(result)).toBe(true);
  });

  it("returns undefined for non-timestamp primitives", () => {
    expect(customizeNode({ node: 42, indexOrName: "count", depth: 1 })).toBeUndefined();
    expect(customizeNode({ node: "hello", indexOrName: "name", depth: 1 })).toBeUndefined();
    expect(customizeNode({ node: true, indexOrName: "ok", depth: 1 })).toBeUndefined();
  });

  it("returns undefined for objects", () => {
    expect(customizeNode({ node: { a: 1 }, indexOrName: "data", depth: 1 })).toBeUndefined();
  });

  it("returns undefined for arrays", () => {
    expect(customizeNode({ node: [1, 2], indexOrName: "items", depth: 1 })).toBeUndefined();
  });
});
