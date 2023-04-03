<script lang="ts">
	// Stores
	import { modalStore } from "@skeletonlabs/skeleton";
	import { jwt } from "$lib/store";
	import { enhance } from "$app/forms";
	import { superValidate } from "sveltekit-superforms/server";
	// import SuperDebug from "sveltekit-superforms/client/SuperDebug.svelte";
	import { registerSchema } from "$lib/validations";

	$: $jwt = $jwt;

	export let parent: never;

	const formData = {
		email: "",
		username: "",
		firstName: "",
		lastName: "",
		password: "",
		confirmPassword: "",
	};
	let errors = {};

	function onFormSubmit(): void {
		if ($modalStore[0].response) $modalStore[0].response(formData);
		modalStore.close();
	}

	const cBase = "card p-4 w-modal shadow-xl space-y-4 max-h-full";
	const cHeader = "text-2xl font-bold";
	const cForm = "border border-surface-500 p-4 space-y-4 rounded-container-token";
	const cInput = "border border-surface-500 p-2 rounded-container-token";
	const cLabel = "text-sm font-bold ";

	const handleSubmission = async () => {
		const form = await superValidate(formData, registerSchema);
		console.log(form);
		if (!form.valid) {
			errors = form.errors;
		}
	};
</script>

<div class={cBase}>
	<header class={cHeader}>{$modalStore[0]?.title ?? "(title missing)"}</header>
	<article>{$modalStore[0]?.body ?? "(body missing)"}</article>
	<!-- Enable for debugging: -->
	<!--	<SuperDebug data={formData} />-->
	<form class="modal-form {cForm}" method="POST" use:enhance>
		<label class="label {cLabel}">
			<span>Email</span>
			{#if errors.email}
				<p class="text-red-500 text-sm">{errors.email}</p>
			{/if}
			<input
				class="input {cInput}"
				type="email"
				bind:value={formData.email}
				placeholder="Enter email address..."
			/>
		</label>

		<label class="label {cLabel}">
			<span>Username</span>
			{#if errors.username}
				<p class="text-red-500 text-sm">{errors.username}</p>
			{/if}
			<input
				class="input {cInput}"
				type="text"
				bind:value={formData.username}
				placeholder="Enter username..."
			/>
		</label>

		<label class="label {cLabel}">
			<span>First Name</span>
			{#if errors.firstName}
				<p class="text-red-500 text-sm">{errors.firstName}</p>
			{/if}
			<input
				class="input {cInput}"
				type="text"
				bind:value={formData.firstName}
				placeholder="Enter first name..."
			/>
		</label>

		<label class="label {cLabel}">
			<span>Last Name</span>
			{#if errors.lastName}
				<p class="text-red-500 text-sm">{errors.lastName}</p>
			{/if}
			<input
				class="input {cInput}"
				type="text"
				bind:value={formData.lastName}
				placeholder="Enter last name..."
			/>
		</label>

		<label class="label {cLabel}">
			<span>Password</span>
			{#if errors.password}
				<p class="text-red-500 text-sm">{errors.password}</p>
			{/if}
			<input
				class="input {cInput}"
				type="password"
				bind:value={formData.password}
				placeholder="Enter password..."
			/>
		</label>

		<label class="label {cLabel}">
			<span>Confirm Password</span>
			{#if errors.confirmPassword}
				<p class="text-red-500 text-sm">{errors.confirmPassword}</p>
			{/if}
			<input
				class="input {cInput}"
				type="password"
				bind:value={formData.confirmPassword}
				placeholder="Enter password..."
			/>
		</label>
	</form>
	<!-- prettier-ignore -->
	<footer class="{parent.regionFooter}">
		<button class="btn {parent.buttonNeutral}" on:click={parent.onClose}>{parent.buttonTextCancel}</button>
		<button class="btn {parent.buttonPositive}" on:click={handleSubmission}>Register</button>
	</footer>
</div>

<style>
	.modal-form {
		overflow-y: auto;
		max-height: 50vh;
	}
</style>
