import { useQuery } from "@tanstack/react-query";
import { refresh } from "@api/auth.js";
import useZuStore from "@store/store.js";
import { useEffect } from "react";

const QUERY = ["refreshToken"];

export const useRefreshToken = ({ refetchInterval }) => {
	const storeInitialized = useZuStore((state) => state.storeInitialized);
	const loginState = useZuStore((state) => state.login);
	const logoutState = useZuStore((state) => state.logout);
	const setUserState = useZuStore((state) => state.setUser);

	const response = useQuery({
		queryKey: QUERY,
		queryFn: ({ signal }) => refresh({ signal }),
		retry: 1,
		retryDelay: 100,
		refetchInterval: refetchInterval,
		refetchIntervalInBackground: !!refetchInterval,
		enabled: storeInitialized,
	});

	useEffect(() => {
		if (response.data) {
			loginState(response.data.user);
			setUserState(response.data.user);
		}

		if (response.error) {
			logoutState();
		}
	}, [loginState, logoutState, response.data, response.error, setUserState]);

	return response;
};
