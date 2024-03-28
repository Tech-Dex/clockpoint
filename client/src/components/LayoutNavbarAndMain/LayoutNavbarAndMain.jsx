import Navbar from "@/components/Navbar/Navbar.jsx";
import styles from "./LayoutNavbarAndMain.module.css";

function LayoutNavbarAndMain({ children }) {
	return (
		<div className={styles.gridArea}>
			<Navbar className={styles.navbarArea} />
			<div className={styles.mainArea}>{children}</div>
		</div>
	);
}

export default LayoutNavbarAndMain;
