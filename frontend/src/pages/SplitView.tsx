import { useCallback } from "react";
import { useSetAtom } from "jotai";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Button from "@mui/material/Button";
import ButtonBase from "@mui/material/ButtonBase";
import Typography from "@mui/material/Typography";
import Skeleton from "@mui/material/Skeleton";
import DeleteIcon from "@mui/icons-material/Delete";
import { styled } from "@mui/material/styles";
import { useQueryClient } from "@tanstack/react-query";
import { Group, Panel, Separator, type Layout } from "react-resizable-panels";
import { darkSurface, dark } from "../theme";
import { useListNavigation } from "../hotkeys/useListNavigation";
import { useGlobalHotkeys } from "../hotkeys/useGlobalHotkeys";
import { useDetailHotkeys } from "../hotkeys/useDetailHotkeys";
import { hotkeyHelpOpenAtom } from "../atoms/hotkeyHelp";
import Kbd from "../components/Kbd";
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

const ResizeHandle = styled(Separator)(({ theme }) => ({
  padding: "0 1px",
  background: theme.palette.divider,
  outline: "none",
}));

const LAYOUT_KEY = "react-resizable-panels:smello-split-view";

function readSavedLayout(): Layout | undefined {
  try {
    const raw = localStorage.getItem(LAYOUT_KEY);
    return raw ? JSON.parse(raw) : undefined;
  } catch {
    return undefined;
  }
}

// Read once at module level so the very first render has the correct layout.
const initialLayout = readSavedLayout();

function SplitViewSkeleton() {
  return (
    <Stack sx={{ height: "100%" }}>
      <Box
        sx={{
          height: 49,
          bgcolor: darkSurface,
          borderBottom: `1px solid ${dark.border}`,
        }}
      />
      <Stack direction="row" sx={{ flex: 1, overflow: "hidden" }}>
        <Box sx={{ width: initialLayout?.list ?? "30%", bgcolor: darkSurface, p: 1 }}>
          {Array.from({ length: 8 }, (_, i) => (
            <Skeleton
              key={i}
              variant="rounded"
              height={40}
              sx={{ mb: 0.5, bgcolor: "rgba(255,255,255,0.05)" }}
            />
          ))}
        </Box>
        <Box sx={{ flex: 1 }} />
      </Stack>
    </Stack>
  );
}

export default function SplitView() {
  const [selectedId] = useSelectedRequestId();
  const queryClient = useQueryClient();
  const setHelpOpen = useSetAtom(hotkeyHelpOpenAtom);
  useListNavigation();
  useGlobalHotkeys();
  useDetailHotkeys();

  const onLayoutChanged = useCallback((layout: Layout) => {
    try {
      localStorage.setItem(LAYOUT_KEY, JSON.stringify(layout));
    } catch {
      // localStorage may be full or unavailable; layout still works, just won't persist.
    }
  }, []);

  const { data: allRequests = [], isLoading } = useListRequestsApiRequestsGet(
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

  if (isLoading) {
    return <SplitViewSkeleton />;
  }

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
        defaultLayout={initialLayout}
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
                spacing={1}
                sx={{ height: "100%", color: "text.disabled" }}
              >
                <Typography>Select a request to view details</Typography>
                <ButtonBase
                  disableRipple
                  onClick={() => setHelpOpen(true)}
                  sx={{ borderRadius: 1, "&:hover": { color: "text.secondary" } }}
                >
                  <Typography variant="body2">
                    Press{" "}
                    <Kbd
                      sx={{
                        color: "text.disabled",
                        borderColor: "divider",
                        bgcolor: "transparent",
                      }}
                    >
                      ?
                    </Kbd>{" "}
                    for keyboard shortcuts
                  </Typography>
                </ButtonBase>
              </Stack>
            )}
          </Box>
        </Panel>
      </Group>
      <ButtonBase
        disableRipple
        onClick={() => setHelpOpen(true)}
        sx={{
          position: "fixed",
          bottom: 12,
          right: 16,
          display: "flex",
          alignItems: "center",
          gap: 0.5,
          px: 1,
          py: 0.5,
          borderRadius: 1,
          color: "text.disabled",
          "&:hover": { color: "text.secondary", bgcolor: "action.hover" },
          transition: "color 150ms, background-color 150ms",
        }}
      >
        <Kbd sx={{ color: "text.disabled", borderColor: "divider", bgcolor: "transparent" }}>?</Kbd>
        <Typography variant="caption" sx={{ fontSize: 11 }}>
          Shortcuts
        </Typography>
      </ButtonBase>
    </Stack>
  );
}
