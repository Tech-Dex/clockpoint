import { useMutation } from "@tanstack/react-query";
import { login } from "@api/auth.js";
import useZuStore from "@store/store.js";

const QUERY = ["login"];

export const useLogin = () => {
	const loginState = useZuStore((state) => state.login);
	const logoutState = useZuStore((state) => state.logout);
	const setUserState = useZuStore((state) => state.setUser);

	return useMutation({
		mutationFn: login,
		mutationKey: QUERY,
		onSuccess: (data) => {
			// Do something with the data
			loginState(data.user);
			setUserState(data.user);
		},
		onError: (error) => {
			logoutState();
			console.error(error);
		},
		onMutate: (variables) => {
			// Do something before the mutation happens
			console.info("Logging in with: ", variables);
		},
	});
};
