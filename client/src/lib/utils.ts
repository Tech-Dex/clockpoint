import { jwt, lastRefresh, user } from "$lib/store";
import type { IUser } from "$lib/store";
import { API } from "$lib/api";
import { get } from "svelte/store";

export const updateStoreJwtAndUser = async (response: Response) => {
	const {
		user: { token, ...data },
	} = await response.json();

	jwt.set(token);
	user.set(data as IUser);
};

export const validateJwt = async (signal: AbortSignal, page = null) => {
	const now = Number(new Date());
	let isPageRefresh = true;
	if (!get(jwt)) return;

	if (page !== null) isPageRefresh = false;
	if (!isPageRefresh && !!get(lastRefresh) && now - (get(lastRefresh) || 0) < 1000 * 60 * 5) return; // 5 minutes

	const response = await API.auth.refresh(signal);
	lastRefresh.set(now);

	if (!response.ok) {
		jwt.set(null);
		return;
	}

	await updateStoreJwtAndUser(response);
	return;
};
