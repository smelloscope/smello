import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import DeleteIcon from "@mui/icons-material/Delete";
import { useQueryClient } from "@tanstack/react-query";
import FilterBar from "../components/FilterBar";
import RequestList from "../components/RequestList";
import RequestDetail from "../components/RequestDetail";
import EmptyState from "../components/EmptyState";
import { useSelectedRequestId } from "../hooks/useSelectedRequestId";
import {
  useListRequestsApiRequestsGet,
  useClearRequestsApiRequestsDelete,
  getListRequestsApiRequestsGetQueryKey,
  getGetMetaApiMetaGetQueryKey,
} from "../api/generated/default/default";

export default function SplitView() {
  const [selectedId] = useSelectedRequestId();
  const queryClient = useQueryClient();

  const { data: allRequests = [] } = useListRequestsApiRequestsGet(
    {},
    { query: { refetchInterval: 3_000 } },
  );

  const clearMutation = useClearRequestsApiRequestsDelete({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({
          queryKey: getListRequestsApiRequestsGetQueryKey(),
        });
        queryClient.invalidateQueries({
          queryKey: getGetMetaApiMetaGetQueryKey(),
        });
      },
    },
  });

  if (allRequests.length === 0) {
    return <EmptyState />;
  }

  return (
    <Stack sx={{ height: "100%" }}>
      <Stack
        direction="row"
        alignItems="center"
        sx={{
          borderBottom: "1px solid",
          borderColor: "divider",
          bgcolor: "background.paper",
        }}
      >
        <Box sx={{ flex: 1 }}>
          <FilterBar />
        </Box>
        <Button
          size="small"
          color="error"
          startIcon={<DeleteIcon />}
          onClick={() => clearMutation.mutate()}
          disabled={clearMutation.isPending}
          sx={{ mr: 1, textTransform: "none" }}
        >
          Clear All
        </Button>
      </Stack>
      <Stack direction="row" sx={{ flex: 1, overflow: "hidden" }}>
        <RequestList />
        <Box sx={{ flex: 1, minHeight: 0, overflow: "auto" }}>
          {selectedId ? (
            <RequestDetail requestId={selectedId} />
          ) : (
            <Stack
              alignItems="center"
              justifyContent="center"
              sx={{ height: "100%", color: "text.disabled" }}
            >
              <Typography>Select a request to view details</Typography>
            </Stack>
          )}
        </Box>
      </Stack>
    </Stack>
  );
}
