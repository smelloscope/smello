import { useState } from "react";
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
      <Stack alignItems="center" sx={{ maxWidth: 520 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
          No captured requests yet
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Install the client and add two lines to start capturing HTTP traffic.
        </Typography>

        <Stack sx={{ width: "100%" }} spacing={2}>
          <div>
            <Stack
              direction="row"
              alignItems="center"
              justifyContent="space-between"
              sx={{ mb: 0.5 }}
            >
              <Typography variant="body2" sx={{ fontWeight: 600, color: "text.secondary" }}>
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
                  sx={{ px: 1.5, py: 0, fontSize: 12, textTransform: "none" }}
                >
                  pip
                </ToggleButton>
                <ToggleButton
                  value="uv"
                  sx={{ px: 1.5, py: 0, fontSize: 12, textTransform: "none" }}
                >
                  uv
                </ToggleButton>
                <ToggleButton
                  value="poetry"
                  sx={{ px: 1.5, py: 0, fontSize: 12, textTransform: "none" }}
                >
                  poetry
                </ToggleButton>
              </ToggleButtonGroup>
            </Stack>
            <Paper variant="outlined">
              <Stack direction="row" alignItems="center" sx={{ p: 2 }}>
                <Typography
                  component="pre"
                  sx={{ fontFamily: "monospace", fontSize: 13, m: 0, flex: 1 }}
                >
                  {installCmd}
                </Typography>
                <CopyButton text={installCmd} />
              </Stack>
            </Paper>
          </div>

          <div>
            <Typography variant="body2" sx={{ fontWeight: 600, color: "text.secondary", mb: 0.5 }}>
              2. Add to your code
            </Typography>
            <Paper variant="outlined">
              <Stack direction="row" alignItems="start" sx={{ p: 2 }}>
                <Typography
                  component="pre"
                  sx={{
                    fontFamily: "monospace",
                    fontSize: 13,
                    m: 0,
                    whiteSpace: "pre-wrap",
                    flex: 1,
                  }}
                >
                  {initCode}
                </Typography>
                <CopyButton text={initCode} />
              </Stack>
            </Paper>
          </div>
        </Stack>

        <Typography variant="body2" color="text.secondary" sx={{ mt: 3 }}>
          Requests will appear here automatically once your code runs.
        </Typography>
      </Stack>
    </Stack>
  );
}
