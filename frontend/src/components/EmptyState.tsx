import { useState } from "react";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Typography from "@mui/material/Typography";
import CopyButton from "./CopyButton";

type PackageManager = "pip" | "uv" | "poetry";

const installCmds: Record<PackageManager, string> = {
  pip: "pip install smello",
  uv: "uv add smello",
  poetry: "poetry add smello",
};

const initCode = `import smello\nsmello.init(server_url="http://localhost:5110")`;

export default function EmptyState() {
  const [pm, setPm] = useState<PackageManager>("pip");
  const installCmd = installCmds[pm];

  return (
    <Stack alignItems="center" justifyContent="center" sx={{ height: "100%", p: 4 }}>
      <Stack alignItems="center" sx={{ maxWidth: 480 }}>
        <Box
          sx={{
            width: 88,
            height: 88,
            borderRadius: "50%",
            bgcolor: "action.hover",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            mb: 2.5,
          }}
        >
          <Box component="img" src="/logo.png" alt="Smello logo" sx={{ width: 56, height: 56 }} />
        </Box>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5 }}>
          No captured requests yet
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3.5 }}>
          Install the client and add two lines to start capturing.
        </Typography>

        <Stack sx={{ width: "100%" }} spacing={1.5}>
          <Stack spacing={0.5}>
            <Stack direction="row" alignItems="center" justifyContent="space-between">
              <Typography
                variant="caption"
                sx={{ fontWeight: 600, color: "text.secondary", letterSpacing: 0.3 }}
              >
                1. Install
              </Typography>
              <ToggleButtonGroup
                value={pm}
                exclusive
                onChange={(_e, v: PackageManager | null) => {
                  if (v) setPm(v);
                }}
                size="small"
              >
                <ToggleButton
                  value="pip"
                  sx={{ px: 1.2, py: 0, fontSize: 11, textTransform: "none", lineHeight: 1.8 }}
                >
                  pip
                </ToggleButton>
                <ToggleButton
                  value="uv"
                  sx={{ px: 1.2, py: 0, fontSize: 11, textTransform: "none", lineHeight: 1.8 }}
                >
                  uv
                </ToggleButton>
                <ToggleButton
                  value="poetry"
                  sx={{ px: 1.2, py: 0, fontSize: 11, textTransform: "none", lineHeight: 1.8 }}
                >
                  poetry
                </ToggleButton>
              </ToggleButtonGroup>
            </Stack>
            <Paper variant="outlined" sx={{ borderRadius: 1.5 }}>
              <Stack direction="row" alignItems="center" sx={{ px: 1.5, py: 1 }}>
                <Typography
                  component="pre"
                  sx={{ fontFamily: "monospace", fontSize: 12.5, m: 0, flex: 1 }}
                >
                  {installCmd}
                </Typography>
                <CopyButton text={installCmd} />
              </Stack>
            </Paper>
          </Stack>

          <Stack spacing={0.5}>
            <Typography
              variant="caption"
              sx={{ fontWeight: 600, color: "text.secondary", letterSpacing: 0.3 }}
            >
              2. Add to your code
            </Typography>
            <Paper variant="outlined" sx={{ borderRadius: 1.5 }}>
              <Stack direction="row" alignItems="start" sx={{ px: 1.5, py: 1 }}>
                <Typography
                  component="pre"
                  sx={{
                    fontFamily: "monospace",
                    fontSize: 12.5,
                    m: 0,
                    whiteSpace: "pre-wrap",
                    flex: 1,
                    lineHeight: 1.6,
                  }}
                >
                  {initCode}
                </Typography>
                <CopyButton text={initCode} />
              </Stack>
            </Paper>
          </Stack>
        </Stack>

        <Typography variant="caption" color="text.disabled" sx={{ mt: 3 }}>
          Requests will appear here automatically once your code runs.
        </Typography>
      </Stack>
    </Stack>
  );
}
