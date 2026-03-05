/**
 * Parse a URL (HTTP or gRPC) into host and path for display.
 *
 * For gRPC URLs like `grpc://host:443/package.Service/Method`,
 * extracts just the `Service/Method` as the display path.
 */
/**
 * Parse query parameters from a URL. Returns an empty array if the URL
 * has no query string or cannot be parsed.
 */
export function parseQueryParams(raw: string): [string, string][] {
  try {
    const url = new URL(raw);
    if (!url.search) return [];
    return [...url.searchParams.entries()];
  } catch {
    return [];
  }
}

export function parseDisplayUrl(raw: string): { host: string; path: string } {
  try {
    // gRPC URLs: grpc://host:port/fully.qualified.Service/Method
    if (raw.startsWith("grpc://")) {
      const withoutScheme = raw.slice(7); // drop "grpc://"
      const slashIdx = withoutScheme.indexOf("/");
      if (slashIdx === -1) return { host: withoutScheme, path: "/" };
      const hostPort = withoutScheme.slice(0, slashIdx);
      const host = hostPort.replace(/:(\d+)$/, ""); // strip port
      const fullPath = withoutScheme.slice(slashIdx);
      // Extract Service/Method from /package.name.Service/Method
      const parts = fullPath.split("/").filter(Boolean);
      if (parts.length >= 2) {
        const service = parts[parts.length - 2]!;
        const method = parts[parts.length - 1]!;
        // Strip package prefix from service: "com.example.FooService" -> "FooService"
        const shortService = service.includes(".")
          ? service.slice(service.lastIndexOf(".") + 1)
          : service;
        return { host, path: `/${shortService}/${method}` };
      }
      return { host, path: fullPath };
    }

    // Standard HTTP(S) URLs
    const url = new URL(raw);
    const host = url.hostname;
    const path = decodeURIComponent(url.pathname + url.search);
    return { host, path: path || "/" };
  } catch {
    return { host: "", path: raw };
  }
}
