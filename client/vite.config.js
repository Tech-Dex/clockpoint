import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import svgr from "vite-plugin-svgr";
import * as path from "path";
// https://vitejs.dev/config/
export default defineConfig({
	plugins: [react(), svgr()],
	resolve: {
		alias: [
			{
				find: "@",
				replacement: path.resolve(__dirname, "./src"),
			},
			{
				find: "@api",
				replacement: path.resolve(__dirname, "./src/api"),
			},
			{
				find: "@components",
				replacement: path.resolve(__dirname, "./src/components"),
			},
			{
				find: "@assets",
				replacement: path.resolve(__dirname, "./src/assets"),
			},
			{
				find: "@hooks",
				replacement: path.resolve(__dirname, "./src/hooks"),
			},
			{
				find: "@pages",
				replacement: path.resolve(__dirname, "./src/pages"),
			},
			{
				find: "@store",
				replacement: path.resolve(__dirname, "./src/store"),
			},
			{
				find: "@utils",
				replacement: path.resolve(__dirname, "./src/utils"),
			},
			{
				find: "@features",
				replacement: path.resolve(__dirname, "./src/features"),
			},
		],
	},
});
