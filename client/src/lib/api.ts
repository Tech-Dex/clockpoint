import { isFetching, jwt } from "$lib/store";
import { get } from "svelte/store";

const DOMAIN = import.meta.env.VITE_API_DOMAIN;
const PORT = import.meta.env.VITE_API_PORT;
const PATH_AUTH = import.meta.env.VITE_API_PATH_AUTH;

export const API = {
	auth: {
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

		login: async function (
			data: {
				email: string;
				password: string;
			},
			signal: AbortSignal,
		) {
			isFetching.set(true);

			const response = await fetch(`${DOMAIN}:${PORT}/${PATH_AUTH}/login`, {
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

		refresh: async function (signal: AbortSignal) {
			return await fetch(`${DOMAIN}:${PORT}/${PATH_AUTH}/refresh`, {
				method: "GET",
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${get(jwt)}`,
				},
				signal: signal,
			});
		},
	},
};
