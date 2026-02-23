import { defineConfig } from "orval";

export default defineConfig({
  smello: {
    input: "./openapi.json",
    output: {
      target: "./src/api/generated/endpoints.ts",
      schemas: "./src/api/generated/model",
      client: "react-query",
      httpClient: "fetch",
      mode: "tags-split",
      override: {
        fetch: {
          includeHttpResponseReturnType: false,
        },
      },
    },
  },
});
