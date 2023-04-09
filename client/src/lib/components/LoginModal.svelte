<script lang="ts">
	// import SuperDebug from "sveltekit-superforms/client/SuperDebug.svelte";
	import { ConicGradient, modalStore } from "@skeletonlabs/skeleton";
	import type { ConicStop } from "@skeletonlabs/skeleton";
	import { isFetching, jwt, user } from "$lib/store";
	import { enhance } from "$app/forms";
	import { superValidate } from "sveltekit-superforms/server";
	import { loginSchema } from "$lib/validations";
	import { API } from "$lib/api";
	import { updateStoreJwtAndUser } from "$lib/utils";

	$: $jwt = $jwt;
	$: $user = $user;
	$: $isFetching = $isFetching;

	export let parent: never;

	const abortController = new AbortController();
	const signal = abortController.signal;

	const formData = {
		email: "",
		password: "",
	};

	let errors = {};

	const conicStops: ConicStop[] = [
		{ color: "transparent", start: 0, end: 25 },
		{ color: "rgb(var(--color-primary-500))", start: 75, end: 100 },
	];

	const cBase = "card p-4 w-modal-slim shadow-xl space-y-4 max-h-full";
	const cHeader = "text-2xl font-bold";
	const cForm = "border border-surface-500 p-4 space-y-4 rounded-container-token";
	const cInput = "border border-surface-500 p-2 rounded-container-token";
	const cLabel = "text-sm font-bold ";

	const handleSubmission = async () => {
		// noinspection TypeScriptValidateTypes
		const form = await superValidate(formData, loginSchema);
		if (!form.valid) {
			errors = form.errors;
			return;
		}

		// handle the api call and jwt in local storage
		{
			const response = await API.auth.login(formData, signal);

			if (!response.ok) {
				// TODO: handle errors from the server in order to point out the specific field
				const serverError = await response.json();
				errors = {
					server: serverError.message,
				};
				return;
			}

			errors = {};

			await updateStoreJwtAndUser(response);
		}

		modalStore.close();
		return;
	};

	const handleCancel = () => {
		abortController.abort();
		$isFetching = false;
		modalStore.close();
	};
</script>

<div class={cBase}>
	<header class={cHeader}>{$modalStore[0]?.title ?? "(title missing)"}</header>
	<article>{$modalStore[0]?.body ?? "(body missing)"}</article>
	{#if errors.server}
		<p class="text-red-500 text-sm">{errors.server}</p>
	{/if}
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
	</form>
	<!-- prettier-ignore -->
	<footer class="{parent.regionFooter}">
		<button class="btn {parent.buttonNeutral}" on:click={handleCancel}>{parent.buttonTextCancel}</button>
		{#if $isFetching}
			<ConicGradient width="w-10" stops={conicStops} spin />
		{:else}
			<button class="btn {parent.buttonPositive} hover:variant-filled-primary" on:click={handleSubmission}>Login
			</button>
		{/if}
	</footer>
</div>

<style>
	.modal-form {
		overflow-y: auto;
		max-height: 60vh;
	}
</style>
