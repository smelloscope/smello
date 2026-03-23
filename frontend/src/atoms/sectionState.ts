import { atom } from "jotai";

export type Side = "request" | "response";

export const headersOpenAtom = {
  request: atom(false),
  response: atom(false),
};

export const bodyOpenAtom = {
  request: atom(true),
  response: atom(true),
};

export const queryParamsOpenAtom = {
  request: atom(false),
  response: atom(false),
};
