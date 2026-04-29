/**
 * Manual API layer for the unified events API.
 * Replaces the Orval-generated hooks for the new event-based endpoints.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { UseQueryOptions, UseMutationOptions } from "@tanstack/react-query";

// --- Types ---

export type EventType = "http" | "log" | "exception";

export interface EventSummary {
  id: string;
  timestamp: string;
  event_type: EventType;
  summary: string;
}

export interface EventDetail extends EventSummary {
  data: Record<string, unknown>;
}

/** HTTP-specific fields inside EventDetail.data */
export interface HttpEventData {
  duration_ms: number;
  method: string;
  url: string;
  host: string;
  request_headers: Record<string, string>;
  request_body: string | null;
  request_body_size: number;
  status_code: number;
  response_headers: Record<string, string>;
  response_body: string | null;
  response_body_size: number;
  library: string;
}

/** Log-specific fields inside EventDetail.data */
export interface LogEventData {
  level: string;
  logger_name: string;
  message: string;
  pathname: string | null;
  lineno: number | null;
  func_name: string | null;
  exc_text: string | null;
  extra: Record<string, unknown> | null;
}

/** Exception-specific fields inside EventDetail.data */
export interface ExceptionEventData {
  exc_type: string;
  exc_value: string;
  exc_module: string | null;
  traceback_text: string;
  frames: Array<{
    filename: string;
    lineno: number;
    function: string;
    context_line: string | null;
    pre_context?: string[];
    post_context?: string[];
  }>;
}

export interface MetaResponse {
  hosts: string[];
  methods: string[];
  event_types: EventType[];
}

export interface ListEventsParams {
  event_type?: string;
  host?: string;
  method?: string;
  status?: number;
  search?: string;
  limit?: number;
}

// --- Fetch functions ---

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  if ([204, 205, 304].includes(res.status)) return {} as T;
  return res.json();
}

function buildUrl(path: string, params?: Record<string, string | number | undefined>): string {
  const url = new URL(path, window.location.origin);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== "") url.searchParams.set(k, String(v));
    }
  }
  return url.toString();
}

export async function listEvents(params?: ListEventsParams): Promise<EventSummary[]> {
  return fetchJson(buildUrl("/api/events", params as Record<string, string | number | undefined>));
}

export async function getEvent(id: string): Promise<EventDetail> {
  return fetchJson(`/api/events/${id}`);
}

export async function getMeta(): Promise<MetaResponse> {
  return fetchJson("/api/meta");
}

export async function clearEvents(): Promise<void> {
  await fetch("/api/events", { method: "DELETE" });
}

// --- Query keys ---

export const eventKeys = {
  all: ["/api/events"] as const,
  list: (params?: ListEventsParams) => ["/api/events", params] as const,
  detail: (id: string) => ["/api/events", id] as const,
  meta: ["/api/meta"] as const,
};

// --- React Query hooks ---

export function useListEvents(
  params?: ListEventsParams,
  options?: Partial<UseQueryOptions<EventSummary[]>>,
) {
  return useQuery({
    queryKey: eventKeys.list(params),
    queryFn: () => listEvents(params),
    ...options,
  });
}

export function useGetEvent(id: string, options?: Partial<UseQueryOptions<EventDetail>>) {
  return useQuery({
    queryKey: eventKeys.detail(id),
    queryFn: () => getEvent(id),
    enabled: !!id,
    ...options,
  });
}

export function useGetMeta(options?: Partial<UseQueryOptions<MetaResponse>>) {
  return useQuery({
    queryKey: eventKeys.meta,
    queryFn: getMeta,
    ...options,
  });
}

export function useClearEvents(options?: UseMutationOptions<void, Error, void>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: clearEvents,
    onSuccess: (...args) => {
      queryClient.invalidateQueries({ queryKey: eventKeys.all });
      queryClient.invalidateQueries({ queryKey: eventKeys.meta });
      options?.onSuccess?.(...args);
    },
    ...options,
  });
}
