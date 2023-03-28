<script lang="ts">
	import { page } from "$app/stores";

	// Skeleton Features
	import { AppShell, AppBar } from "@skeletonlabs/skeleton";
	import type { DrawerSettings } from "@skeletonlabs/skeleton";
	import { Drawer, drawerStore } from "@skeletonlabs/skeleton";

	// Local Features
	import Navigation from "$lib/components/Navigation.svelte";

	// Stylesheets
	import "@skeletonlabs/skeleton/themes/theme-crimson.css";
	import "@skeletonlabs/skeleton/styles/all.css";
	import "../app.postcss";
	import "$globalCss";

	const drawerSettings: DrawerSettings = {
		id: "main-drawer",
		position: "left",
		// CSS Classes
		bgDrawer: "bg-surface-900 text-white",
		bgBackdrop: "bg-gradient-to-l bg-surface-500/50",
		width: "w-[280px] md:w-[480px]",
		rounded: "rounded-r-2xl",
	};

	function drawerOpen(): void {
		drawerStore.open(drawerSettings);
	}

	// Reactive Properties
	$: classesSidebarLeft = $page.url.pathname === "/" ? "w-0" : "w-0";
</script>

<!-- Drawer -->
<Drawer>
	<h2 class="p-4">Navigation</h2>
	<hr />
	<Navigation />
</Drawer>

<!-- App Shell -->
<AppShell slotSidebarLeft="bg-surface-500/5 {classesSidebarLeft}">
	<svelte:fragment slot="header">
		<!-- App Bar -->
		<AppBar>
			<svelte:fragment slot="lead">
				<div class="flex items-center">
					<button class="lg btn btn-sm mr-4" on:click={drawerOpen}>
						<span>
							<svg viewBox="0 0 100 80" class="fill-token w-4 h-4">
								<rect width="100" height="20" />
								<rect y="30" width="100" height="20" />
								<rect y="60" width="100" height="20" />
							</svg>
						</span>
					</button>
					<strong class="text-xl uppercase">Skeleton</strong>
				</div>
			</svelte:fragment>
			<svelte:fragment slot="trail">
				<a class="btn btn-sm" href="/">Home</a>
				<a class="btn btn-sm" href="/about">About</a>
			</svelte:fragment>
		</AppBar>
	</svelte:fragment>
	<!-- Left Sidebar Slot -->
	<svelte:fragment slot="sidebarLeft">
		<Navigation />
	</svelte:fragment>
	<!-- Page Route Content -->
	<slot />
</AppShell>
