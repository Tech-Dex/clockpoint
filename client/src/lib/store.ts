import { localStorageStore } from "@skeletonlabs/skeleton";
import type { Writable } from "svelte/store";

export const jwt: Writable<string | null> = localStorageStore("jwt", null);
