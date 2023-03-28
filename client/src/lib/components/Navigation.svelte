<script lang="ts">
	import { drawerStore } from "@skeletonlabs/skeleton";
	function drawerClose(): void {
		drawerStore.close();
	}
</script>

<nav class="list-nav p-4">
	<ul>
		<li class="bg-surface-500 rounded-2xl"><a href="/" on:click={drawerClose}>Homepage</a></li>
		<li><a href="/about" on:click={drawerClose}>About</a></li>
		<li><a href="/login" on:click={drawerClose}>Login</a></li>
		<li><a href="/register" on:click={drawerClose}>Register</a></li>
	</ul>
</nav>
