import { localStorageStore } from "@skeletonlabs/skeleton";
import type { Writable } from "svelte/store";

export interface IUser {
	email: string;
	firstName: string;
	secondName: string | null;
	lastName: string;
	username: string;
	isActive: boolean;
	phoneNumber: string | null;
}

export const isFetching: Writable<boolean> = localStorageStore("isFetching", false);
export const jwt: Writable<string | null> = localStorageStore("jwt", null);
export const user: Writable<IUser | null> = localStorageStore("user", null);
