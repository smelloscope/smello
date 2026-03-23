import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import List from "@mui/material/List";
import Typography from "@mui/material/Typography";
import { darkSurface, dark } from "../theme";
import { useSelectedRequestId } from "../hooks/useSelectedRequestId";
import { useFilteredRequests } from "../hooks/useFilteredRequests";
import RequestListItem from "./RequestListItem";

export default function RequestList() {
  const [selectedId, setSelectedId] = useSelectedRequestId();
  const { data: requests = [] } = useFilteredRequests();

  return (
    <Box
      sx={{
        height: "100%",
        overflowY: "auto",
        overscrollBehavior: "none",
        bgcolor: darkSurface,
        color: dark.textPrimary,
      }}
    >
      {requests.length === 0 ? (
        <Stack
          alignItems="center"
          justifyContent="center"
          sx={{ height: "100%", p: 3, color: dark.textMuted }}
        >
          <Typography variant="body2">No matching requests</Typography>
        </Stack>
      ) : (
        <List disablePadding>
          {requests.map((item) => (
            <RequestListItem
              key={item.id}
              item={item}
              selected={item.id === selectedId}
              onClick={() => setSelectedId(item.id)}
            />
          ))}
        </List>
      )}
    </Box>
  );
}
