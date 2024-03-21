import { Link } from "react-router-dom";

// ChatGPT goes brrrr
const NotFound = () => {
	return (
		<div style={styles.container}>
			<h2 style={styles.title}>404 - Not Found</h2>
			<p style={styles.description}>
				Sorry, the page you are looking for might be in another castle.
			</p>
			<Link to='/' style={styles.link}>
				Go back to Home
			</Link>
		</div>
	);
};

const styles = {
	container: {
		textAlign: "center",
		padding: "50px",
		fontFamily: "Arial, sans-serif",
	},
	title: {
		fontSize: "3em",
		margin: "0",
		color: "#333",
	},
	description: {
		fontSize: "1.2em",
		color: "#555",
		marginTop: "10px",
	},
	link: {
		display: "inline-block",
		marginTop: "20px",
		padding: "10px 20px",
		backgroundColor: "#3498db",
		color: "#fff",
		textDecoration: "none",
		borderRadius: "5px",
		fontSize: "1.2em",
	},
};

export default NotFound;
