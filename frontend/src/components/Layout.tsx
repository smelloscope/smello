import type { ReactNode } from "react";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <Stack sx={{ height: "100vh" }}>
      <Stack
        direction="row"
        alignItems="center"
        spacing={1}
        sx={{
          px: 2,
          py: 1,
          borderBottom: "1px solid",
          borderColor: "divider",
          bgcolor: "background.paper",
        }}
      >
        <Stack
          component="a"
          href="/"
          direction="row"
          alignItems="center"
          spacing={1}
          sx={{ textDecoration: "none", color: "inherit" }}
        >
          <Box component="img" src="/logo.png" alt="Smello" sx={{ width: 24, height: 24 }} />
          <Typography variant="h6" sx={{ fontWeight: 700, fontSize: 16 }}>
            Smello
          </Typography>
        </Stack>
        <Typography variant="body2" sx={{ color: "text.secondary", fontSize: 12 }}>
          HTTP Request Inspector
        </Typography>
      </Stack>
      <Box sx={{ flex: 1, overflow: "hidden" }}>{children}</Box>
    </Stack>
  );
}
