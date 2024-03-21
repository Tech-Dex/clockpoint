import { Link } from "react-router-dom";
import { CustomSlider } from "@components/CustomSlider/CustomSlider.jsx";
import { CustomDatePicker } from "@components/CustomDatePicker/CustomDatePicker.jsx";

function Page2() {
	return (
		<div>
			<h1>Page 2</h1>
			<Link to='/page1'>Go to Page 1</Link>
			<br />
			<Link to='/page2'>Go to Page 2</Link>
			<br />
			<Link to='/'>Root</Link>
			<br />
			<CustomSlider />
			<br />
			<br />
			<CustomDatePicker />
		</div>
	);
}

export default Page2;
