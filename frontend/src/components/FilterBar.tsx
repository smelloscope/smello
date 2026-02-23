import { useAtom } from "jotai";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import InputAdornment from "@mui/material/InputAdornment";
import SearchIcon from "@mui/icons-material/Search";
import { hostFilterAtom, methodFilterAtom, searchFilterAtom } from "../atoms/filters";
import { useGetMetaApiMetaGet } from "../api/generated/default/default";

export default function FilterBar() {
  const [host, setHost] = useAtom(hostFilterAtom);
  const [method, setMethod] = useAtom(methodFilterAtom);
  const [search, setSearch] = useAtom(searchFilterAtom);

  const { data: meta } = useGetMetaApiMetaGet({
    query: { refetchInterval: 10_000 },
  });

  return (
    <Stack direction="row" spacing={1} alignItems="center" sx={{ p: 1 }}>
      <TextField
        size="small"
        placeholder="Search URLs..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          },
        }}
        sx={{ minWidth: 200, flex: 1 }}
      />
      <FormControl size="small" sx={{ minWidth: 140 }}>
        <InputLabel>Host</InputLabel>
        <Select value={host} label="Host" onChange={(e) => setHost(e.target.value)}>
          <MenuItem value="">All hosts</MenuItem>
          {meta?.hosts.map((h) => (
            <MenuItem key={h} value={h}>
              {h}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <FormControl size="small" sx={{ minWidth: 100 }}>
        <InputLabel>Method</InputLabel>
        <Select value={method} label="Method" onChange={(e) => setMethod(e.target.value)}>
          <MenuItem value="">All</MenuItem>
          {meta?.methods.map((m) => (
            <MenuItem key={m} value={m}>
              {m}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Stack>
  );
}
