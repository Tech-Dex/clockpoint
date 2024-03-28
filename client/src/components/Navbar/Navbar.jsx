import LogoSvg from "@assets/logo.svg?react";
import LoginSvg from "@assets/login.svg?react";
import styles from "./Navbar.module.css";
import { useMediaQuery } from "@uidotdev/usehooks";
import { MOBILE_MEDIA_QUERY } from "@/utils/breakpoints.js";
import classNames from "classnames";

function Navbar() {
	const isMobile = useMediaQuery(MOBILE_MEDIA_QUERY);

	return (
		<nav className={styles.navGrid}>
			<div className={styles.logoArea}>
				<LogoSvg className={styles.logo} onClick={() => alert("Logo")} />
			</div>
			<div className={classNames(styles.navLinksArea, styles.navLinksGrid)}>
				<div className={styles.registerArea}>
					<div className={styles.registerAlign}>
						<button
							className={styles.registerButton}
							onClick={() => {
								alert("Start Campaign");
							}}
						>
							Start Campaign
						</button>
					</div>
				</div>
				{isMobile ? (
					<div className={styles.loginArea}>
						<LoginSvg className={styles.loginLogo} />
					</div>
				) : (
					<div className={styles.loginArea}>
						<div className={styles.loginAlign}>
							{/*TODO: Create a button component that accepts css classes as props and a default hover effect*/}
							<button
								className={styles.loginButton}
								onClick={() => {
									alert("Login");
								}}
							>
								Login
							</button>
						</div>
					</div>
				)}
			</div>
		</nav>
	);
}

export default Navbar;
