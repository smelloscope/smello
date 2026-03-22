import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import DeleteIcon from "@mui/icons-material/Delete";
import { styled } from "@mui/material/styles";
import { darkSurface, dark } from "../theme";
import { Group, Panel, Separator, useDefaultLayout } from "react-resizable-panels";

const ResizeHandle = styled(Separator)(({ theme }) => ({
  padding: "0 1px",
  background: theme.palette.divider,
  outline: "none",
}));
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

  const { defaultLayout, onLayoutChanged } = useDefaultLayout({
    id: "smello-split-view",
    storage: localStorage,
  });

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
          bgcolor: darkSurface,
          color: dark.textPrimary,
          borderBottom: `1px solid ${dark.border}`,
        }}
      >
        <Box component="a" href="/" sx={{ display: "flex", alignItems: "center", pl: 1.5 }}>
          <Box component="img" src="/logo-dark.png" alt="Smello" sx={{ width: 24, height: 24 }} />
        </Box>
        <Box sx={{ flex: 1 }}>
          <FilterBar />
        </Box>
        <Button
          size="small"
          variant="outlined"
          startIcon={<DeleteIcon />}
          onClick={() => clearMutation.mutate()}
          disabled={clearMutation.isPending}
          sx={{
            mr: 1,
            textTransform: "none",
            height: 40,
            color: "#ff8a80",
            borderColor: "rgba(255,138,128,0.4)",
            "&:hover": {
              borderColor: "#ff8a80",
              bgcolor: "rgba(255,138,128,0.08)",
            },
          }}
        >
          Clear All
        </Button>
      </Stack>
      <Group
        orientation="horizontal"
        defaultLayout={defaultLayout}
        onLayoutChanged={onLayoutChanged}
        style={{ flex: 1, overflow: "hidden" }}
      >
        <Panel id="list" defaultSize="30%" minSize="15%" maxSize="50%">
          <RequestList />
        </Panel>
        <ResizeHandle />
        <Panel id="detail" minSize="30%">
          <Box sx={{ height: "100%", minHeight: 0, overflow: "auto" }}>
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
        </Panel>
      </Group>
    </Stack>
  );
}
