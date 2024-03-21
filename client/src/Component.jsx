import "@/App.css";
import { useLogin } from "@features/auth/api/use-login.jsx";
import { useRegister } from "@features/auth/api/use-register.jsx";
import useZuStore from "@store/store.js";

function Component() {
	const authToken = useZuStore((state) => state.auth?.token);
	const user = useZuStore((state) => state.user);

	const {
		mutate: mutateLogin,
		isLoading: isLoadingLogin,
		isError: isErrorLogin,
		error: errorLogin,
	} = useLogin();

	const {
		mutate: mutateRegister,
		isLoading: isLoadingRegister,
		isError: isErrorRegister,
		error: errorRegister,
	} = useRegister();

	const handleLogin = () => {
		mutateLogin({
			email: "Tyler.Hermiston14@gmail.com",
			password: "defaultPassword1!",
			options: {
				/* Any additional options you want to pass */
			},
		});
		mutateLogin({
			email: "Tyler.Hermiston14@gmail.com",
			password: "defaultPassword1!",
			options: {
				/* Any additional options you want to pass */
			},
		});
	};

	const handleRegister = () => {
		mutateRegister({
			email: "alexandru@fake.com",
			password: "defaultPassword1!",
			username: "alexandru",
			firstName: "Alexandru",
			lastName: "Fake",
		});
	};

	if (authToken) {
		return <div>Data current {JSON.stringify(user)}</div>;
	}

	return (
		<>
			<div>
				<button onClick={handleLogin} disabled={isLoadingLogin}>
					{isLoadingLogin ? "Logging in..." : "Login"}
				</button>
				{isErrorLogin && <div>Error: {errorLogin.message}</div>}
			</div>

			<div>
				<button onClick={handleRegister} disabled={isLoadingRegister}>
					{isLoadingRegister ? "Registering..." : "Register"}
				</button>
				{isErrorRegister && <div>Error: {errorRegister.message}</div>}
			</div>
		</>
	);
}

export default Component;
