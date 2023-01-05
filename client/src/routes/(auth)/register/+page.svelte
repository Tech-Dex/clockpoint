<script lang="ts">
	import { enhance } from "$app/forms";
	import type { ActionData } from "./$types";

	export let form: ActionData;
</script>

<svelte:head>
	<title>User Registration</title>
</svelte:head>

<hgroup>
	<h1>Sign in</h1>
	<h2>Join into the magical world of Clockpoint</h2>
</hgroup>
<form use:enhance method="POST">
	{#if form?.errors}
		<details>
			<summary>Errors</summary>
			<ul>
				{#each Object.values(form.errors) as error}
					<li>{error}</li>
				{/each}
			</ul>
		</details>
	{/if}
	<fieldset class="form-group">
		<input
			type="text"
			name="email"
			id="email"
			placeholder="Email"
			aria-label="email"
			autocomplete="email"
			class:warning={form?.errors?.email}
			value={form?.data?.email ?? ""}
			required
		/>
		<input
			type="text"
			name="username"
			placeholder="Username"
			aria-label="username"
			autocomplete="username"
			class:warning={form?.errors?.username}
			value={form?.data?.username ?? ""}
			required
		/>
		<input
			type="text"
			name="firstName"
			placeholder="First Name"
			aria-label="firstName"
			autocomplete="given-name"
			class:warning={form?.errors?.firstName}
			value={form?.data?.firstName ?? ""}
			required
		/>
		<input
			type="text"
			name="lastName"
			placeholder="Last Name"
			aria-label="lastName"
			autocomplete="family-name"
			class:warning={form?.errors?.lastName}
			value={form?.data?.lastName ?? ""}
			required
		/>

		<input
			type="password"
			name="password"
			placeholder="Password"
			aria-label="password"
			autocomplete="current-password"
			class:warning={form?.errors?.password || form?.errors?.confirmPassword}
			value={form?.data?.password ?? ""}
			required
		/>
		<input
			type="password"
			name="confirmPassword"
			placeholder="Confirm Password"
			aria-label="confirmPassword"
			autocomplete="current-password"
			class:warning={form?.errors?.confirmPassword || form?.errors?.password}
			value={form?.data?.confirmPassword ?? ""}
			required
		/>
	</fieldset>
	<button type="submit">Register</button>
</form>

<style>
	.form-group {
		display: grid;
		grid-template-columns: 1fr 1fr;
		grid-column-gap: 1rem;
	}

	.form-group input:last-child {
		grid-column: 1 / 3;
	}

	.form-group input:nth-last-child(2) {
		grid-column: 1 / 3;
	}

	@media (max-width: 768px) {
		.form-group {
			grid-template-columns: 1fr;
		}
		.form-group input:last-of-type {
			grid-column: 1;
		}
	}
</style>
