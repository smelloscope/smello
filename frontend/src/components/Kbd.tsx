import Box from "@mui/material/Box";
import type { SxProps, Theme } from "@mui/material/styles";
import { dark, mono } from "../theme";

type KbdProps = {
  children: React.ReactNode;
  sx?: SxProps<Theme>;
};

export default function Kbd({ children, sx }: KbdProps) {
  return (
    <Box
      component="kbd"
      sx={{
        display: "inline-block",
        fontFamily: mono,
        fontSize: 11,
        fontWeight: 600,
        lineHeight: "20px",
        minWidth: 20,
        textAlign: "center",
        px: 0.75,
        py: 0,
        borderRadius: "4px",
        border: "1px solid",
        borderColor: dark.divider,
        bgcolor: dark.hover,
        color: dark.textSecondary,
        ...sx,
      }}
    >
      {children}
    </Box>
  );
}
