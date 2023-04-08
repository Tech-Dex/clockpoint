import { isFetching } from "$lib/store";

const DOMAIN = import.meta.env.VITE_API_DOMAIN;
const PORT = import.meta.env.VITE_API_PORT;
const PATH_AUTH = import.meta.env.VITE_API_PATH_AUTH;
export const API = {
	register: async function (
		data: {
			firstName: string;
			lastName: string;
			password: string;
			confirmPassword: string;
			email: string;
			username: string;
		},
		signal: AbortSignal,
	) {
		isFetching.set(true);

		const response = await fetch(`${DOMAIN}:${PORT}/${PATH_AUTH}/register`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify(data),
			signal: signal,
		});

		isFetching.set(false);

		return response;
	},
};
