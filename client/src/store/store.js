import { create } from "zustand";
import localforage from "localforage";
import { devtools } from "zustand/middleware";

let createStore;

if (import.meta.env.VITE_ENV === "development") {
	// Import devtools only in development

	createStore = devtools(create);
} else {
	// Use create without devtools in production
	createStore = create;
}

const useZuStore = createStore((set) => ({
	storeInitialized: false,
	auth: {
		token: null,
		email: null,
	},
	preferences: {
		theme: "light",
	},
	user: {
		username: null,
		firstName: null,
		secondName: null,
		lastName: null,
		loadedAt: null,
	},

	// Actions

	login: async ({ token, email }) => {
		set({ auth: { token, email } });
		await localforage.setItem("auth", { token, email });
	},

	logout: async () => {
		set({ auth: { token: null, email: null } });
		await localforage.setItem("auth", { token: null, email: null });
	},

	setTheme: async (theme) => {
		if (!["light", "dark"].includes(theme)) {
			return;
		}

		set({ preferences: { theme } });
		await localforage.setItem("preferences", { theme });
	},

	setUser: ({ username, firstName, secondName, lastName }) => {
		const now = new Date();
		set({ user: { username, firstName, secondName, lastName, loadedAt: now } });
	},

	setState: async (persistedState) => {
		set(persistedState);

		const { auth, preferences } = persistedState;

		await Promise.all([
			localforage.setItem("auth", auth),
			localforage.setItem("preferences", preferences),
		]);
	},
}));

const hydrateStore = async () => {
	const [auth, preferences] = await Promise.all([
		localforage.getItem("auth"),
		localforage.getItem("preferences"),
	]);

	useZuStore.setState({ auth, preferences });
};

hydrateStore().then(() => {
	useZuStore.setState({ storeInitialized: true });
	if (import.meta.env.VITE_ENV === "development") {
		console.info("State hydrated from local storage");
		console.table(
			Object.entries(useZuStore.getState()).map(([key, value]) => ({
				key,
				value,
			})),
		);
	}
});

export default useZuStore;
