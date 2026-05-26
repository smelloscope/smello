import { useAtom } from "jotai";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import InputAdornment from "@mui/material/InputAdornment";
import SearchIcon from "@mui/icons-material/Search";
import { dark } from "../theme";
import {
  hostFilterAtom,
  methodFilterAtom,
  searchFilterAtom,
  eventTypeFilterAtom,
  appFilterAtom,
  sessionFilterAtom,
} from "../atoms/filters";
import { useGetMeta } from "../api/events";
import EventTypeIcon from "./EventTypeIcon";
import type { EventType } from "../api/events";

export default function FilterBar() {
  const [host, setHost] = useAtom(hostFilterAtom);
  const [method, setMethod] = useAtom(methodFilterAtom);
  const [search, setSearch] = useAtom(searchFilterAtom);
  const [eventType, setEventType] = useAtom(eventTypeFilterAtom);
  const [app, setApp] = useAtom(appFilterAtom);
  const [session, setSession] = useAtom(sessionFilterAtom);

  const { data: meta } = useGetMeta({ refetchInterval: 10_000 });

  const darkSelect = {
    color: dark.textPrimary,
    ".MuiOutlinedInput-notchedOutline": { borderColor: dark.divider },
    "&:hover .MuiOutlinedInput-notchedOutline": { borderColor: dark.textDisabled },
    ".MuiSvgIcon-root": { color: dark.textMuted },
  };

  const eventTypeLabels: Record<string, string> = {
    http: "HTTP (outgoing)",
    http_incoming: "HTTP (incoming)",
    log: "Logs",
    exception: "Exceptions",
  };

  return (
    <Stack direction="row" spacing={1} alignItems="center" sx={{ p: 1 }}>
      <Select
        size="small"
        displayEmpty
        value={eventType}
        onChange={(e) => setEventType(e.target.value)}
        sx={{ minWidth: 130, ...darkSelect }}
        renderValue={(v) => {
          if (!v) return "All types";
          return (
            <Stack direction="row" alignItems="center" spacing={0.75}>
              <EventTypeIcon eventType={v as EventType} dark size={16} />
              <span>{eventTypeLabels[v] ?? v}</span>
            </Stack>
          );
        }}
      >
        <MenuItem value="">All types</MenuItem>
        {meta?.event_types.map((t) => (
          <MenuItem key={t} value={t}>
            <Stack direction="row" alignItems="center" spacing={1}>
              <EventTypeIcon eventType={t} size={18} />
              <span>{eventTypeLabels[t] ?? t}</span>
            </Stack>
          </MenuItem>
        ))}
      </Select>
      <Select
        size="small"
        displayEmpty
        value={method}
        onChange={(e) => setMethod(e.target.value)}
        sx={{ minWidth: 90, ...darkSelect }}
        renderValue={(v) => v || "Method"}
      >
        <MenuItem value="">All methods</MenuItem>
        {meta?.methods.map((m) => (
          <MenuItem key={m} value={m}>
            {m}
          </MenuItem>
        ))}
      </Select>
      <Select
        size="small"
        displayEmpty
        value={host}
        onChange={(e) => setHost(e.target.value)}
        sx={{ minWidth: 140, ...darkSelect }}
        renderValue={(v) => v || "Host"}
      >
        <MenuItem value="">All hosts</MenuItem>
        {meta?.hosts.map((h) => (
          <MenuItem key={h} value={h}>
            {h}
          </MenuItem>
        ))}
      </Select>
      <Select
        size="small"
        displayEmpty
        value={app ?? "__all__"}
        onChange={(e) => {
          const v = e.target.value;
          setApp(v === "__all__" ? undefined : v);
        }}
        sx={{ minWidth: 100, ...darkSelect }}
        renderValue={(v) => {
          if (v === "__all__") return "App";
          if (v === "") return "(no app)";
          return v;
        }}
      >
        <MenuItem value="__all__">All apps</MenuItem>
        {meta?.apps?.includes("") && <MenuItem value="">(no app)</MenuItem>}
        {meta?.apps
          ?.filter((a) => a !== "")
          .map((a) => (
            <MenuItem key={a} value={a}>
              {a}
            </MenuItem>
          ))}
      </Select>
      <Select
        size="small"
        displayEmpty
        value={session ?? "__all__"}
        onChange={(e) => {
          const v = e.target.value;
          setSession(v === "__all__" ? undefined : v);
        }}
        sx={{ minWidth: 110, ...darkSelect }}
        renderValue={(v) => {
          if (v === "__all__") return "Session";
          if (v === "") return "(no session)";
          return v.length > 12 ? v.slice(0, 8) + "…" : v;
        }}
        title={session ?? ""}
      >
        <MenuItem value="__all__">All sessions</MenuItem>
        {meta?.sessions?.includes("") && <MenuItem value="">(no session)</MenuItem>}
        {meta?.sessions
          ?.filter((s) => s !== "")
          .map((s) => (
            <MenuItem key={s} value={s} title={s}>
              {s.length > 24 ? s.slice(0, 20) + "…" : s}
            </MenuItem>
          ))}
      </Select>
      <TextField
        size="small"
        placeholder="Search events...  (/)"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" sx={{ color: dark.textMuted }} />
              </InputAdornment>
            ),
          },
          htmlInput: {
            "data-hotkey-target": "search",
          },
        }}
        sx={{
          minWidth: 200,
          flex: 1,
          "& .MuiOutlinedInput-root": {
            color: dark.textPrimary,
            "& .MuiOutlinedInput-notchedOutline": { borderColor: dark.divider },
            "&:hover .MuiOutlinedInput-notchedOutline": { borderColor: dark.textDisabled },
          },
          "& .MuiInputBase-input::placeholder": { color: dark.textDisabled, opacity: 1 },
        }}
      />
    </Stack>
  );
}
