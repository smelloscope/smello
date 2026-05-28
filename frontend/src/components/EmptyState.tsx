import { useState } from "react";
import Box from "@mui/material/Box";
import Link from "@mui/material/Link";
import Stack from "@mui/material/Stack";
import Paper from "@mui/material/Paper";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Typography from "@mui/material/Typography";
import CopyButton from "./CopyButton";
import { useGetMeta } from "../api/events";

type PackageManager = "pip" | "uv" | "poetry";

const installCmds: Record<PackageManager, string> = {
  pip: "pip install smello",
  uv: "uv add smello",
  poetry: "poetry add smello",
};

const runCmds: Record<PackageManager, string> = {
  pip: "smello run ./my_script.py",
  uv: "uv run smello run ./my_script.py",
  poetry: "poetry run smello run ./my_script.py",
};

export default function EmptyState() {
  const [pm, setPm] = useState<PackageManager>("pip");
  const { data: meta } = useGetMeta();
  const installCmd = installCmds[pm];
  const runCmd = runCmds[pm];

  return (
    <Stack alignItems="center" justifyContent="center" sx={{ height: "100%", p: 4 }}>
      <Stack alignItems="center" sx={{ maxWidth: { xs: 480, lg: 640 }, width: "100%" }}>
        <Box
          sx={{
            width: { xs: 112, lg: 140 },
            height: { xs: 112, lg: 140 },
            borderRadius: "50%",
            bgcolor: "action.hover",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            mb: { xs: 3, lg: 4 },
          }}
        >
          <Box
            component="img"
            src="/logo.png"
            alt="Smello logo"
            sx={{ width: { xs: 72, lg: 88 }, height: { xs: 72, lg: 88 } }}
          />
        </Box>
        <Typography variant="h5" sx={{ fontWeight: 700, mb: 0.5, fontSize: { lg: "1.8rem" } }}>
          No captured requests yet
        </Typography>
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{ mb: { xs: 4, lg: 5 }, fontSize: { lg: "1.05rem" } }}
        >
          Install the client and run your script to start capturing.
        </Typography>

        <Stack sx={{ width: "100%" }} spacing={{ xs: 2, lg: 2.5 }}>
          <Stack spacing={0.75}>
            <Stack direction="row" alignItems="center" justifyContent="space-between">
              <Typography
                variant="body2"
                sx={{
                  fontWeight: 600,
                  color: "text.secondary",
                  letterSpacing: 0.3,
                  fontSize: { lg: 14 },
                }}
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
                  sx={{
                    px: 1.5,
                    py: 0.25,
                    fontSize: { xs: 12, lg: 13 },
                    textTransform: "none",
                    lineHeight: 1.8,
                  }}
                >
                  pip
                </ToggleButton>
                <ToggleButton
                  value="uv"
                  sx={{
                    px: 1.5,
                    py: 0.25,
                    fontSize: { xs: 12, lg: 13 },
                    textTransform: "none",
                    lineHeight: 1.8,
                  }}
                >
                  uv
                </ToggleButton>
                <ToggleButton
                  value="poetry"
                  sx={{
                    px: 1.5,
                    py: 0.25,
                    fontSize: { xs: 12, lg: 13 },
                    textTransform: "none",
                    lineHeight: 1.8,
                  }}
                >
                  poetry
                </ToggleButton>
              </ToggleButtonGroup>
            </Stack>
            <Paper variant="outlined" sx={{ borderRadius: 1.5 }}>
              <Stack direction="row" alignItems="center" sx={{ px: 2, py: { xs: 1.25, lg: 1.5 } }}>
                <Typography
                  component="pre"
                  sx={{ fontFamily: "monospace", fontSize: { xs: 13.5, lg: 15 }, m: 0, flex: 1 }}
                >
                  {installCmd}
                </Typography>
                <CopyButton text={installCmd} />
              </Stack>
            </Paper>
          </Stack>

          <Stack spacing={0.75}>
            <Typography
              variant="body2"
              sx={{
                fontWeight: 600,
                color: "text.secondary",
                letterSpacing: 0.3,
                fontSize: { lg: 14 },
              }}
            >
              2. Run your script
            </Typography>
            <Paper variant="outlined" sx={{ borderRadius: 1.5 }}>
              <Stack direction="row" alignItems="center" sx={{ px: 2, py: { xs: 1.25, lg: 1.5 } }}>
                <Typography
                  component="pre"
                  sx={{ fontFamily: "monospace", fontSize: { xs: 13.5, lg: 15 }, m: 0, flex: 1 }}
                >
                  {runCmd}
                </Typography>
                <CopyButton text={runCmd} />
              </Stack>
            </Paper>
          </Stack>
        </Stack>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mt: { xs: 4, lg: 5 }, fontSize: { lg: "0.95rem" } }}
        >
          Requests will appear here automatically once your code runs.
        </Typography>
        <Stack direction="row" spacing={1.5} sx={{ mt: 1.5 }}>
          <Link
            href="https://smello.io/getting-started/"
            target="_blank"
            rel="noopener"
            variant="body2"
            underline="hover"
            sx={{ fontWeight: 500, fontSize: { lg: "0.95rem" } }}
          >
            Read the docs
          </Link>
          <Typography variant="body2" color="text.disabled" sx={{ fontSize: { lg: "0.95rem" } }}>
            ·
          </Typography>
          <Link
            href="https://github.com/smelloscope/smello"
            target="_blank"
            rel="noopener"
            variant="body2"
            underline="hover"
            sx={{ fontWeight: 500, fontSize: { lg: "0.95rem" } }}
          >
            Star us on GitHub
          </Link>
        </Stack>
        {meta?.server_version && (
          <Typography variant="caption" color="text.disabled" sx={{ mt: 2 }}>
            smello-server v{meta.server_version}
          </Typography>
        )}
      </Stack>
    </Stack>
  );
}
