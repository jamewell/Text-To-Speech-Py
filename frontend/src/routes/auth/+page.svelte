<script lang="ts">
	import { authStore } from '../../stores/auth';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	// Redirect if already authenticated, otherwise redirect to login
	onMount(() => {
		if ($authStore.isAuthenticated) {
			goto('/profile');
		} else {
			goto('/login');
		}
	});
</script>

<svelte:head>
	<title>Account - TTS Studio</title>
</svelte:head>

<div class="mx-auto max-w-md px-4 py-12 sm:px-6 lg:px-8">
	<div class="card py-12 text-center">
		<svg
			class="mx-auto mb-4 h-12 w-12 animate-spin text-blue-600"
			xmlns="http://www.w3.org/2000/svg"
			fill="none"
			viewBox="0 0 24 24"
		>
			<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
			></circle>
			<path
				class="opacity-75"
				fill="currentColor"
				d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
			></path>
		</svg>
		<p class="text-gray-600">Redirecting...</p>
	</div>
</div>
