import LogoSvg from "@assets/logo.svg?react";
import LoginSvg from "@assets/login.svg?react";
import styles from "./Navbar.module.css";
import { useMediaQuery } from "@uidotdev/usehooks";

function Navbar() {
	const isSm = useMediaQuery("(min-width: 640px)");

	return (
		<nav className={`${styles.gridArea} bg-primary drop-shadow-xl px-4 sm:px-0`}>
			<div className={`${styles.logoArea} flex items-center justify-center`}>
				<LogoSvg className={"max-h-full max-w-full"} />
			</div>
			<div
				className={`${styles.registerArea} flex items-center justify-end sm:justify-start`}
			>
				<button
					className={
						"bg-cyrannus-secondary w-3/4 h-1/2  lg:w-2/4 text-inherit text-sm lg:text-lg"
					}
				>
					Start Campaign
				</button>
			</div>
			{isSm ? (
				<div className={`${styles.loginArea} flex items-center justify-end`}>
					<button className={'w-3/4 h-1/2  lg:w-2/4 text-inherit text-sm lg:text-lg"'}>
						Login
					</button>
				</div>
			) : (
				<div className={`${styles.loginArea} flex items-center justify-start`}>
					<LoginSvg className={"max-h-full max-w-full"} />
				</div>
			)}
		</nav>
	);
}

export default Navbar;
