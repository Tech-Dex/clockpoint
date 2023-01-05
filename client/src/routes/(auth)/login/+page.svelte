<script lang="ts">
	import { enhance } from "$app/forms";
</script>

<svelte:head>
	<title>User Login</title>
</svelte:head>

<hgroup>
	<h1>Login</h1>
	<h2>Jump into the magical world of Clockpoint</h2>
</hgroup>
<form use:enhance>
	<fieldset class="form-group">
		<input
			type="text"
			name="email"
			placeholder="Email"
			aria-label="email"
			autocomplete="email"
			required
		/>
		<input
			type="password"
			name="password"
			placeholder="Password"
			aria-label="password"
			autocomplete="current-password"
			required
		/>
	</fieldset>
	<button type="submit">Register</button>
</form>
