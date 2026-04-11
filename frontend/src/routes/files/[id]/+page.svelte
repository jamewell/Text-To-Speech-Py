<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import FileAudioPlayer from '$lib/components/player/FileAudioPlayer.svelte';
	import { api, type ApiError } from '$lib/api';
	import type { FileDetail } from '$lib/schemas/api';
	import { authStore } from '../../../stores/auth';

	let file: FileDetail | null = null;
	let isLoading = true;
	let errorMessage = '';

	function getFileIdFromPath(): number | null {
		if (typeof window === 'undefined') {
			return null;
		}

		const segments = window.location.pathname.split('/').filter(Boolean);
		const fileId = Number(segments[segments.length - 1]);
		return Number.isInteger(fileId) && fileId > 0 ? fileId : null;
	}

	async function loadFile(): Promise<void> {
		const fileId = getFileIdFromPath();
		if (fileId === null) {
			errorMessage = 'Invalid file id.';
			isLoading = false;
			return;
		}

		if (!$authStore.isAuthenticated) {
			goto('/login');
			return;
		}

		try {
			file = await api.getFile(fileId);
		} catch (error) {
			const apiError = error as ApiError;
			if (apiError.isAuthError) {
				goto('/login');
				return;
			}

			if (apiError.status === 404) {
				errorMessage = 'This file was not found or you do not have access to it.';
			} else {
				errorMessage = apiError.message || 'Failed to load file details.';
			}
		} finally {
			isLoading = false;
		}
	}

	onMount(() => {
		void loadFile();
	});
</script>

<svelte:head>
	<title>File Player - TTS Studio</title>
</svelte:head>

<div class="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
	<div class="mb-8">
		<p class="text-sm font-medium text-blue-700">Playback</p>
		<h1 class="mt-2 text-3xl font-bold text-gray-900">File Player</h1>
		<p class="mt-2 text-gray-600">Listen chapter by chapter and keep your place automatically.</p>
	</div>

	{#if isLoading}
		<div class="card py-12 text-center">
			<p class="text-lg font-medium text-gray-900">Loading file...</p>
			<p class="mt-2 text-sm text-gray-500">Fetching file details and playback state.</p>
		</div>
	{:else if errorMessage}
		<div class="card">
			<h2 class="text-xl font-semibold text-gray-900">Playback unavailable</h2>
			<p class="mt-3 text-gray-600">{errorMessage}</p>
		</div>
	{:else if file}
		{#if file.status === 'processing' || file.status === 'pending'}
			<div class="card">
				<h2 class="text-xl font-semibold text-gray-900">This file is still processing</h2>
				<p class="mt-3 text-gray-600">
					The PDF is still being parsed or converted to audio. Open this page again once processing is complete.
				</p>
			</div>
		{:else if file.status === 'failed'}
			<div class="card">
				<h2 class="text-xl font-semibold text-gray-900">Processing failed</h2>
				<p class="mt-3 text-gray-600">
					{file.error_message || 'The backend reported a processing failure for this file.'}
				</p>
			</div>
		{:else if file.chapters.length === 0}
			<div class="card">
				<h2 class="text-xl font-semibold text-gray-900">No chapters available</h2>
				<p class="mt-3 text-gray-600">
					This file completed processing but no chapters are available for playback yet.
				</p>
			</div>
		{:else}
			<FileAudioPlayer {file} />
		{/if}
	{/if}
</div>
