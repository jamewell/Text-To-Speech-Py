<script lang="ts">
	import { goto } from '$app/navigation';
	import { authStore } from '../../stores/auth';
	import { onMount } from 'svelte';

	onMount(() => {
		if (!$authStore.isAuthenticated) {
			goto('/login');
		}
	});

	function formatDate(dateString: string): string {
		const date = new Date(dateString);
		return date.toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}

	function getDaysSinceJoined(dateString: string): number {
		const joinDate = new Date(dateString);
		const today = new Date();
		const diffTime = Math.abs(today.getTime() - joinDate.getTime());
		const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

		return diffDays;
	}

	async function handleLogout() {
		await authStore.logout();
	}
</script>

<svelte:head>
	<title>Profile - TTS Studio</title>
</svelte:head>

<div class="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="mb-2 text-3xl font-bold text-gray-900">👤 My Profile</h1>
		<p class="text-gray-600">Manage your account settings and preferences</p>
	</div>

	{#if $authStore.user}
		<div class="space-y-6">
			<!-- Account Information Card -->
			<div class="card">
				<div class="mb-2 flex items-start justify-between">
					<div>
						<h2 class="mb-1 text-xl font-semibold text-gray-900">Account Information</h2>
						<p class="text-sm text-gray-500">Your personal account details</p>
					</div>
					<div
						class="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600"
					>
						<span class="text-2xl font-bold text-white">
							{$authStore.user.email.charAt(0).toUpperCase()}
						</span>
					</div>
				</div>

				<div class="space-y-4">
					<div class="flex items-center justify-between border-b border-gray-200 py-3">
						<div>
							<p class="text-sm font-medium text-gray-500">Email</p>
							<p class="mt-1 text-base text-gray-900">{$authStore.user.email}</p>
						</div>
						<span
							class="inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-800"
						>
							✓ Verified
						</span>
					</div>

					<div class="flex items-center justify-between border-b border-gray-200 py-3">
						<div>
							<p class="text-sm font-medium text-gray-500">Member Since</p>
							<p class="mt-1 text-base text-gray-900">
								{formatDate($authStore.user.created_at)}
							</p>
						</div>
						<span
							class="inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-800"
						>
							{getDaysSinceJoined($authStore.user.created_at)} days ago
						</span>
					</div>

					<div class="flex items-center justify-between border-b border-gray-200 py-3">
						<div>
							<p class="text-sm font-medium text-gray-500">Account Status</p>
							<p class="mt-1 text-base text-gray-900">
								{$authStore.user.is_active ? 'Active' : 'Inactive'}
							</p>
						</div>
						{#if $authStore.user.is_active}
							<span
								class="inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-800"
							>
								Active
							</span>
						{:else}
							<span
								class="inline-flex items-center rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-800"
							>
								Inactive
							</span>
						{/if}
					</div>

					<div class="flex items-center justify-between py-3">
						<div>
							<p class="text-sm font-medium text-gray-500">User Id</p>
							<p class="mt-1 text-base text-gray-900">{$authStore.user.id}</p>
						</div>
					</div>
				</div>
			</div>

			<!-- Usage Statistics -->
			<div class="card">
				<h2 class="mb-4 text-xl font-semibold text-gray-900">📊 Usage Statistics</h2>
				<div class="grid gap-6 md:grid-cols-3">
					<div class="rounded-lg bg-blue-50 p-4 text-center">
						<div class="mb-2 text-3xl font-bold text-blue-600">0</div>
						<p class="text-sm text-gray-600">Total Conversions</p>
					</div>
					<div class="rounded-lg bg-blue-50 p-4 text-center">
						<div class="mb-2 text-3xl font-bold text-blue-600">0</div>
						<p class="text-sm text-gray-600">Audio Files</p>
					</div>
					<div class="rounded-lg bg-blue-50 p-4 text-center">
						<div class="mb-2 text-3xl font-bold text-blue-600">0</div>
						<p class="text-sm text-gray-600">Storage Used</p>
					</div>
				</div>
				<p class="mt-4 text-center text-sm text-gray-500">
					Statistics will be updated as you use the service
				</p>
			</div>

			<!-- Quick actions card -->
			<div class="card">
				<h2 class="mb-4 text-xl font-semibold text-gray-900">⚡ Quick Actions</h2>
				<div class="grid gap-4 md:grid-cols-2">
					<a
						href="/upload"
						class="group flex items-center rounded-lg border border-gray-200 p-4 transition-all hover:border-blue-500 hover:bg-blue-50"
					>
						<span class="mr-4 text-3xl">📤</span>
						<div>
							<h3 class="font-medium text-gray-900 group-hover:text-blue-600">Upload Text</h3>
							<p class="text-sm text-gray-500">Convert new text to speech</p>
						</div>
					</a>
					<a
						href="/dashboard"
						class="group flex items-center rounded-lg border border-gray-200 p-4 transition-all hover:border-blue-500 hover:bg-blue-50"
					>
						<span class="mr-4 text-3xl">📊</span>
						<div>
							<h3 class="font-medium text-gray-900 group-hover:text-blue-600">View Dashboard</h3>
							<p class="text-sm text-gray-500">Manage your projects</p>
						</div>
					</a>
				</div>
			</div>

			<!-- Account actions card -->
			<div class="card">
				<h2 class="mb-4 text-xl font-semibold text-gray-900">Account Settings</h2>
				<div class="space-y-3">
					<button
						class="flex w-full items-center justify-between rounded-lg border border-gray-200 p-4 text-left transition-colors hover:bg-gray-50"
					>
						<div class="flex items-center">
							<span class="mr-4 text-2xl">🔑</span>
							<div>
								<h3 class="font-medium text-gray-900">Change Password</h3>
								<p class="text-sm text-gray-500">Update your password</p>
							</div>
						</div>
						<span class="text-gray-400">→</span>
					</button>

					<button
						class="flex w-full items-center justify-between rounded-lg border border-gray-200 p-4 text-left transition-colors hover:bg-gray-50"
					>
						<div class="flex items-center">
							<span class="mr-4 text-2xl">🔔</span>
							<div>
								<h3 class="font-medium text-gray-900">Notification</h3>
								<p class="text-sm text-gray-500">Manage notification preferences</p>
							</div>
						</div>
						<span class="text-gray-400">→</span>
					</button>

					<button
						on:click={handleLogout}
						class="flex w-full items-center justify-between rounded-lg border border-gray-200 p-4 text-left transition-colors hover:bg-gray-50"
					>
						<div class="flex items-center">
							<span class="mr-4 text-2xl">🚪</span>
							<div>
								<h3 class="font-medium text-red-600 group-hover:text-red-700">Sign out</h3>
								<p class="text-sm text-gray-500">Log out of your account</p>
							</div>
						</div>
						<span class="text-red-400">→</span>
					</button>
				</div>
			</div>
		</div>
	{:else}
		<!-- Loading state -->
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
			<p class="text-gray-600">Loading profile...</p>
		</div>
	{/if}
</div>
