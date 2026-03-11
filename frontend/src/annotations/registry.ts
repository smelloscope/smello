import type { Annotator } from "./types";
import { detectUnixSeconds, detectUnixMs } from "./timestamp";

export const defaultAnnotators: Annotator[] = [detectUnixSeconds, detectUnixMs];
