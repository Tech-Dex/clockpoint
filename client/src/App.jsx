import "@/App.css";
import { useRefreshToken } from "@features/auth/api/use-refresh-token.jsx";
import Component from "@/Component.jsx";

function App() {
	const {
		data: dataRefreshToken,
		isLoading: isLoadingRefreshToken,
		isError: isErrorRefreshToken,
		error: errorRefreshToken,
	} = useRefreshToken({ refetchInterval: import.meta.env.VITE_REFETCH_TOKEN_INTERVAL });

	if (isLoadingRefreshToken) {
		return <div>Loading...</div>;
	}

	return (
		<>
			<Component />
		</>
	);
}

export default App;
