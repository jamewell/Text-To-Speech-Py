<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import { api, type ApiError } from '$lib/api';
	import { authStore } from '../../stores/auth';
	import { isOnline } from '$lib/stores/network';
	import type { FileUploadResponse } from '$lib/schemas/api';

	const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024;

	let selectedFile: File | null = null;
	let fileInput: HTMLInputElement | null = null;
	let isUploading = false;
	let uploadProgress = 0;
	let isDragActive = false;
	let validationError = '';
	let uploadError = '';
	let uploadSuccess = '';
	let uploadedFile: FileUploadResponse | null = null;

	onMount(() => {
		if (!$authStore.isAuthenticated) {
			goto('/login');
		}
	});

	function validateFile(file: File): string {
		if (file.size > MAX_FILE_SIZE_BYTES) {
			return 'File too large. Maximum size is 50MB.';
		}

		const isPdfByMime = file.type === 'application/pdf';
		const isPdfByExtension = file.name.toLowerCase().endsWith('.pdf');
		if (!isPdfByMime && !isPdfByExtension) {
			return 'Only PDF files are allowed.';
		}

		return '';
	}

	function processSelectedFile(file: File | null): void {
		validationError = '';
		uploadError = '';
		uploadSuccess = '';
		uploadedFile = null;

		if (!file) {
			selectedFile = null;
			return;
		}

		const error = validateFile(file);
		if (error) {
			validationError = error;
			selectedFile = null;
			if (fileInput) {
				fileInput.value = '';
			}
			return;
		}

		selectedFile = file;
	}

	function handleFileSelection(event: Event): void {
		const input = event.currentTarget as HTMLInputElement;
		const file = input.files?.[0] ?? null;
		processSelectedFile(file);
	}

	function handleDragOver(event: DragEvent): void {
		event.preventDefault();
		isDragActive = true;
	}

	function handleDragLeave(event: DragEvent): void {
		event.preventDefault();
		isDragActive = false;
	}

	function handleDrop(event: DragEvent): void {
		event.preventDefault();
		isDragActive = false;
		if (isUploading) {
			return;
		}

		const file = event.dataTransfer?.files?.[0] ?? null;
		processSelectedFile(file);
	}

	function clearSelection(): void {
		selectedFile = null;
		validationError = '';
		uploadError = '';
		uploadSuccess = '';
		uploadedFile = null;
		uploadProgress = 0;
		if (fileInput) {
			fileInput.value = '';
		}
	}

	function formatBytes(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
	}

	async function handleUpload(event: Event): Promise<void> {
		event.preventDefault();

		if (!$authStore.isAuthenticated) {
			goto('/login');
			return;
		}

		if (!$isOnline) {
			uploadError = 'You are offline. Reconnect and try again.';
			return;
		}

		if (!selectedFile) {
			validationError = 'Please select a PDF file first.';
			return;
		}

		isUploading = true;
		uploadError = '';
		uploadSuccess = '';
		uploadedFile = null;
		uploadProgress = 0;

		try {
			const response = await api.uploadFile(selectedFile, (progress: number) => {
				uploadProgress = progress;
			});
			uploadedFile = response;
			uploadSuccess = `Uploaded "${response.original_filename}" successfully.`;
			if (fileInput) {
				fileInput.value = '';
			}
			selectedFile = null;
		} catch (error) {
			const apiError = error as ApiError;
			if (apiError.isAuthError) {
				goto('/login');
				return;
			}
			uploadError = apiError.message || 'Upload failed. Please try again.';
		} finally {
			isUploading = false;
		}
	}
</script>

<svelte:head>
	<title>Upload - TTS Studio</title>
</svelte:head>

<div class="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
	<div class="mb-8 text-center">
		<h1 class="mt-4 mb-4 text-3xl font-bold text-gray-900">📤 Upload & Convert</h1>
		<p class="text-lg text-gray-600">Upload a PDF file to start text-to-speech processing</p>
	</div>

	<div class="card">
		<form on:submit={handleUpload} class="space-y-6">
			<div>
				<label for="pdf-file" class="mb-2 block text-sm font-medium text-gray-700">
					PDF File
				</label>
				<div
					class="rounded-lg border-2 border-dashed p-6 text-center transition-colors {isDragActive
						? 'border-blue-500 bg-blue-50'
						: 'border-gray-300 bg-gray-50'}"
					role="region"
					aria-label="PDF upload dropzone"
					on:dragover={handleDragOver}
					on:dragleave={handleDragLeave}
					on:drop={handleDrop}
				>
					<p class="text-sm text-gray-700">Drag and drop a PDF here, or use the picker below.</p>
				</div>
				<input
					bind:this={fileInput}
					id="pdf-file"
					type="file"
					accept="application/pdf,.pdf"
					on:change={handleFileSelection}
					disabled={isUploading}
					class="block w-full text-sm text-gray-700 file:mr-4 file:rounded-md file:border-0 file:bg-blue-50 file:px-4 file:py-2 file:font-medium file:text-blue-700 hover:file:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-60"
				/>
				<p class="mt-2 text-sm text-gray-500">Max size: 50MB. Allowed type: PDF.</p>
			</div>

			{#if isUploading}
				<div>
					<div class="mb-1 flex items-center justify-between text-sm text-gray-600">
						<span>Upload progress</span>
						<span>{uploadProgress}%</span>
					</div>
					<div class="h-2 w-full rounded-full bg-gray-200">
						<div
							class="h-2 rounded-full bg-blue-600 transition-all duration-150"
							style="width: {uploadProgress}%"
						></div>
					</div>
				</div>
			{/if}

			{#if selectedFile}
				<div class="rounded-lg border border-blue-200 bg-blue-50 p-4">
					<p class="text-sm text-blue-900">
						<span class="font-semibold">Selected:</span>
						{selectedFile.name}
					</p>
					<p class="mt-1 text-sm text-blue-800">
						{formatBytes(selectedFile.size)}
					</p>
				</div>
			{/if}

			{#if validationError}
				<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
					{validationError}
				</div>
			{/if}

			{#if uploadError}
				<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
					{uploadError}
				</div>
			{/if}

			{#if uploadSuccess}
				<div class="rounded-lg border border-green-200 bg-green-50 p-4">
					<p class="text-sm font-medium text-green-800">{uploadSuccess}</p>
					{#if uploadedFile}
						<p class="mt-1 text-sm text-green-700">Status: {uploadedFile.status}</p>
						<p class="mt-1 text-sm text-green-700">
							Uploaded: {new Date(uploadedFile.upload_date).toLocaleString()}
						</p>
					{/if}
				</div>
			{/if}

			<div class="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
				<Button type="button" variant="secondary" on:click={clearSelection} disabled={isUploading}>
					Clear
				</Button>
				<Button
					type="submit"
					loading={isUploading}
					loadingText="Uploading..."
					disabled={!selectedFile}
				>
					Upload PDF
				</Button>
			</div>
		</form>
	</div>

	<div class="card mt-6">
		<h2 class="mb-3 text-lg font-semibold text-gray-900">Notes</h2>
		<ul class="space-y-2 text-sm text-gray-600">
			<li>• Duplicate filenames are rejected by the backend.</li>
			<li>• You must stay logged in while uploading.</li>
			<li>• Processing starts after successful upload.</li>
		</ul>
	</div>
</div>
