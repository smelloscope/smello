import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useListNavigation } from "../useListNavigation";

// Mock filtered requests
const mockRequests = [
  {
    id: "a",
    method: "GET",
    url: "http://x/1",
    status_code: 200,
    duration_ms: 10,
    timestamp: "",
    library: "requests",
    request_body_size: 0,
    response_body_size: 0,
  },
  {
    id: "b",
    method: "POST",
    url: "http://x/2",
    status_code: 201,
    duration_ms: 20,
    timestamp: "",
    library: "requests",
    request_body_size: 0,
    response_body_size: 0,
  },
  {
    id: "c",
    method: "GET",
    url: "http://x/3",
    status_code: 200,
    duration_ms: 30,
    timestamp: "",
    library: "requests",
    request_body_size: 0,
    response_body_size: 0,
  },
];

vi.mock("../../hooks/useFilteredRequests", () => ({
  useFilteredRequests: () => ({ data: mockRequests }),
}));

let currentHash = "";
vi.mock("../../hooks/useSelectedRequestId", () => ({
  useSelectedRequestId: () => [
    currentHash || null,
    (id: string | null) => {
      currentHash = id ?? "";
    },
  ],
}));

// Stub react-hotkeys-hook to capture callbacks
const hotkeyCallbacks: Record<string, () => void> = {};
vi.mock("react-hotkeys-hook", () => ({
  useHotkeys: (keys: string, callback: () => void) => {
    for (const key of keys.split(",").map((k) => k.trim())) {
      hotkeyCallbacks[key] = callback;
    }
  },
}));

beforeEach(() => {
  currentHash = "";
  Object.keys(hotkeyCallbacks).forEach((k) => delete hotkeyCallbacks[k]);
});

describe("useListNavigation", () => {
  it("selects first item when nothing is selected and j is pressed", () => {
    renderHook(() => useListNavigation());
    act(() => hotkeyCallbacks["j"]!());
    expect(currentHash).toBe("a");
  });

  it("selects last item when nothing is selected and k is pressed", () => {
    renderHook(() => useListNavigation());
    act(() => hotkeyCallbacks["k"]!());
    expect(currentHash).toBe("c");
  });

  it("moves to next item with j", () => {
    currentHash = "a";
    renderHook(() => useListNavigation());
    act(() => hotkeyCallbacks["j"]!());
    expect(currentHash).toBe("b");
  });

  it("moves to previous item with k", () => {
    currentHash = "b";
    renderHook(() => useListNavigation());
    act(() => hotkeyCallbacks["k"]!());
    expect(currentHash).toBe("a");
  });

  it("clamps at the end (does not wrap)", () => {
    currentHash = "c";
    renderHook(() => useListNavigation());
    act(() => hotkeyCallbacks["j"]!());
    expect(currentHash).toBe("c");
  });

  it("clamps at the beginning (does not wrap)", () => {
    currentHash = "a";
    renderHook(() => useListNavigation());
    act(() => hotkeyCallbacks["k"]!());
    expect(currentHash).toBe("a");
  });

  it("registers ArrowDown and ArrowUp as aliases", () => {
    renderHook(() => useListNavigation());
    expect(hotkeyCallbacks["ArrowDown"]).toBeDefined();
    expect(hotkeyCallbacks["ArrowUp"]).toBeDefined();
  });
});
