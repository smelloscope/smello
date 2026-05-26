import { atom } from "jotai";

export const hostFilterAtom = atom<string>("");
export const methodFilterAtom = atom<string>("");
export const searchFilterAtom = atom<string>("");
export const eventTypeFilterAtom = atom<string>("");
export const appFilterAtom = atom<string | undefined>(undefined);
export const sessionFilterAtom = atom<string | undefined>(undefined);
