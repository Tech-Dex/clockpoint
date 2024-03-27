import "@/App.css";
import { useRefreshToken } from "@features/auth/api/use-refresh-token.jsx";
import LayoutNavbarAndMain from "@/components/LayoutNavbarAndMain/LayoutNavbarAndMain.jsx";
import LoginForm from "@/features/auth/components/LoginForm/LoginForm.jsx";

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
			<LayoutNavbarAndMain>
				{/*<Component />*/}
				<div className='grid justify-center items-center h-full'>
					<LoginForm />
				</div>
			</LayoutNavbarAndMain>
		</>
	);
}

export default App;
