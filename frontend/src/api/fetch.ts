/**
 * Patch global fetch to throw on non-OK HTTP responses.
 *
 * Orval's generated fetch client doesn't check `res.ok`, so a 404
 * silently parses the error body as valid data. This wrapper ensures
 * TanStack Query sees a thrown error and surfaces it via `isError`.
 *
 * Call once in main.tsx before rendering.
 */
export function installFetchInterceptor() {
  const originalFetch = window.fetch;

  window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const res = await originalFetch(input, init);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status} ${res.statusText}`);
    }
    return res;
  };
}
