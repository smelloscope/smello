import { useAtom } from "jotai";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import CloseIcon from "@mui/icons-material/Close";
import { hotkeyHelpOpenAtom } from "../atoms/hotkeyHelp";
import { dark, darkSurface } from "../theme";
import { HOTKEYS } from "./registry";
import type { HotkeyGroup } from "./types";
import Kbd from "../components/Kbd";

const GROUP_ORDER: HotkeyGroup[] = ["General", "Navigation", "Filters", "Detail"];

/** Deduplicate entries that share a description within the same group (e.g. j and ArrowDown). */
function deduplicatedEntries(group: HotkeyGroup) {
  const entries = HOTKEYS.filter((h) => h.group === group);
  const seen = new Map<string, { labels: string[]; description: string }>();
  for (const entry of entries) {
    const existing = seen.get(entry.description);
    if (existing) {
      existing.labels.push(entry.label);
    } else {
      seen.set(entry.description, { labels: [entry.label], description: entry.description });
    }
  }
  return [...seen.values()];
}

export default function HotkeyHelpDialog() {
  const [open, setOpen] = useAtom(hotkeyHelpOpenAtom);

  return (
    <Dialog
      open={open}
      onClose={() => setOpen(false)}
      maxWidth="sm"
      fullWidth
      slotProps={{
        paper: {
          sx: { bgcolor: darkSurface, color: dark.textPrimary, backgroundImage: "none" },
        },
      }}
    >
      <DialogTitle
        component="div"
        sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", pb: 0 }}
      >
        <Typography variant="h6" component="span" sx={{ fontWeight: 700 }}>
          Keyboard Shortcuts
        </Typography>
        <IconButton size="small" onClick={() => setOpen(false)} sx={{ color: dark.textSecondary }}>
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>
      <DialogContent sx={{ pt: 2 }}>
        <Stack spacing={2.5}>
          {GROUP_ORDER.map((group) => {
            const rows = deduplicatedEntries(group);
            if (rows.length === 0) return null;
            return (
              <Box key={group}>
                <Typography
                  variant="overline"
                  sx={{
                    color: dark.textSecondary,
                    fontWeight: 700,
                    letterSpacing: 1.5,
                    mb: 0.5,
                    display: "block",
                  }}
                >
                  {group}
                </Typography>
                <Stack spacing={0.5}>
                  {rows.map((row) => (
                    <Stack
                      key={row.description}
                      direction="row"
                      alignItems="center"
                      justifyContent="space-between"
                      sx={{ py: 0.5 }}
                    >
                      <Typography variant="body2" sx={{ color: dark.textPrimary }}>
                        {row.description}
                      </Typography>
                      <Stack direction="row" spacing={0.5} alignItems="center">
                        {row.labels.map((label, i) => (
                          <span key={label}>
                            {i > 0 && (
                              <Typography
                                component="span"
                                variant="caption"
                                sx={{ color: dark.textDisabled, mx: 0.5 }}
                              >
                                /
                              </Typography>
                            )}
                            <Kbd>{label}</Kbd>
                          </span>
                        ))}
                      </Stack>
                    </Stack>
                  ))}
                </Stack>
              </Box>
            );
          })}
        </Stack>
      </DialogContent>
    </Dialog>
  );
}
