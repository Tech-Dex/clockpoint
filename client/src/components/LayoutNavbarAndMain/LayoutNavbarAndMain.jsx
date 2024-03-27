import Navbar from "@/components/Navbar/Navbar.jsx";
import styles from "./LayoutNavbarAndMain.module.css";

function LayoutNavbarAndMain({ children }) {
	return (
		<div className={`${styles.gridArea}`}>
			<div className={`${styles.navbarArea}`}>
				<Navbar />
			</div>
			<div className={`${styles.mainArea} bg-primary`}>{children}</div>
		</div>
	);
}

export default LayoutNavbarAndMain;
