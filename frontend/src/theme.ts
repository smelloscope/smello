import { createTheme } from "@mui/material/styles";

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
        },
      },
    },
  },
});

export default theme;
