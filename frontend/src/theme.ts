import { createTheme } from "@mui/material/styles";

const mono = "'SF Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace";

const theme = createTheme({
  typography: {
    fontSize: 13,
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
  },
  palette: {
    background: {
      default: "#f5f5f5",
    },
  },
  components: {
    MuiTableCell: {
      styleOverrides: {
        root: {
          padding: "4px 8px",
          fontSize: 13,
          fontFamily: mono,
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          "&.Mui-selected": {
            backgroundColor: "rgba(0, 0, 0, 0.04)",
          },
          "&.Mui-selected:hover": {
            backgroundColor: "rgba(0, 0, 0, 0.06)",
          },
        },
      },
    },
  },
});

export default theme;
