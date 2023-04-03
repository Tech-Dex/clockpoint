<script lang="ts">
	import { page } from "$app/stores";

	// Skeleton Features
	import { AppShell, AppBar, Modal } from "@skeletonlabs/skeleton";
	import type { DrawerSettings, ModalSettings } from "@skeletonlabs/skeleton";
	import { Drawer, drawerStore } from "@skeletonlabs/skeleton";
	import { LightSwitch } from "@skeletonlabs/skeleton";
	import { modalStore } from "@skeletonlabs/skeleton";

	// Local Features
	import Navigation from "$lib/components/Navigation.svelte";
	import RegisterModal from "$lib/components/RegisterModal.svelte";

	// Stylesheets
	import "@skeletonlabs/skeleton/themes/theme-crimson.css";
	import "@skeletonlabs/skeleton/styles/all.css";
	import "../app.postcss";
	import "$globalCss";
	import { onMount } from "svelte";

	// Reactive Properties
	$: classesSidebarLeft = $page.url.pathname === "/" ? "w-0" : "w-0";

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

	const modals: Record<string, RegisterModal> = {
		registerModal: {
			ref: RegisterModal,
		},
	};

	const onRegisterOpen = () => {
		modalStore.trigger({
			type: "component",
			component: "registerModal",
			title: "Create an Account",
			body: "Be part of the community!",
		});
	};
</script>

<!-- Drawer -->
<Drawer>
	<h2 class="p-4">Navigation</h2>
	<hr />
	<Navigation />
</Drawer>

<Modal components={modals} />

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
					<strong class="text-xl uppercase">Clockpoint</strong>
				</div>
			</svelte:fragment>
			<svelte:fragment slot="trail">
				<LightSwitch />
				<a class="btn btn-sm" href="/">Home</a>
				<button class="btn btn-sm" on:click={onRegisterOpen}>Register</button>
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
