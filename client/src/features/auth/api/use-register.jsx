import { useMutation } from "@tanstack/react-query";
import { register } from "@api/auth.js";
import useZuStore from "@store/store.js";
const QUERY = ["register"];

export const useRegister = () => {
	const loginState = useZuStore((state) => state.login);
	const logoutState = useZuStore((state) => state.logout);
	const setUserState = useZuStore((state) => state.setUser);

	return useMutation({
		mutationFn: register,
		mutationKey: QUERY,
		onSuccess: (data) => {
			// Do something with the data
			console.info("Registered with: ", data);
			loginState(data.user);
			setUserState(data.user);
		},
		onError: (error) => {
			logoutState();
			console.error(error);
		},
		onMutate: (variables) => {
			// Do something before the mutation happens
			console.info("Registering with: ", variables);
		},
	});
};
