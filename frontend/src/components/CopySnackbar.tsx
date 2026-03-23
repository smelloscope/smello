import { useAtom } from "jotai";
import Snackbar from "@mui/material/Snackbar";
import { dark, darkSurface } from "../theme";
import { snackbarMessageAtom } from "../atoms/snackbar";

export default function CopySnackbar() {
  const [message, setMessage] = useAtom(snackbarMessageAtom);

  return (
    <Snackbar
      open={!!message}
      autoHideDuration={1500}
      onClose={() => setMessage(null)}
      message={message}
      anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      slotProps={{
        content: {
          sx: { bgcolor: darkSurface, color: dark.textPrimary, minWidth: "auto" },
        },
      }}
    />
  );
}
