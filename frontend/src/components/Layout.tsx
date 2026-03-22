import type { ReactNode } from "react";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <Stack sx={{ height: "100vh" }}>
      <Box sx={{ flex: 1, overflow: "hidden" }}>{children}</Box>
    </Stack>
  );
}
