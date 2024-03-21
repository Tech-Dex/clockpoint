import { Link, useMatches, useNavigate, useSearchParams } from "react-router-dom";

function Page1() {
	const navigate = useNavigate();
	const matches = useMatches();
	let [searchParams, setSearchParams] = useSearchParams();
	console.log(matches);
	console.log(searchParams);

	return (
		<div>
			<h1>Page 1</h1>
			<Link to='/page1'>Go to Page 1</Link>
			<br />
			<Link to='/page2'>Go to Page 2</Link>
			<br />
			<Link to='/'>Root</Link>
			<br />
			<button onClick={() => navigate("/page2")}>Go to Page 2 with button</button>
		</div>
	);
}

export default Page1;
