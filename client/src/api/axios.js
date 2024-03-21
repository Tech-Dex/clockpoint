import Axios from "axios";
import useZuStore from "@store/store.js";

const axios = Axios.create({
	baseURL: import.meta.env.VITE_API_DOMAIN_V1,
});

axios.interceptors.request.use(
	(config) => {
		const { auth } = useZuStore.getState();
		const token = auth?.token;

		if (token) {
			config.headers.Authorization = `Bearer ${token}`;
		}
		return config;
	},
	(error) => {
		return Promise.reject(error);
	},
);

export { axios };
