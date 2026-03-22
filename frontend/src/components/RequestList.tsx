import { useAtomValue } from "jotai";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import List from "@mui/material/List";
import Typography from "@mui/material/Typography";
import { darkSurface, dark } from "../theme";
import { useListRequestsApiRequestsGet } from "../api/generated/default/default";
import { hostFilterAtom, methodFilterAtom, searchFilterAtom } from "../atoms/filters";
import { useSelectedRequestId } from "../hooks/useSelectedRequestId";
import RequestListItem from "./RequestListItem";

export default function RequestList() {
  const host = useAtomValue(hostFilterAtom);
  const method = useAtomValue(methodFilterAtom);
  const search = useAtomValue(searchFilterAtom);
  const [selectedId, setSelectedId] = useSelectedRequestId();

  const { data: requests = [] } = useListRequestsApiRequestsGet(
    {
      ...(host ? { host } : {}),
      ...(method ? { method } : {}),
      ...(search ? { search } : {}),
    },
    {
      query: { refetchInterval: 3_000 },
    },
  );

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
