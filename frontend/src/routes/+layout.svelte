<script lang="ts">
	import '../app.css';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { authStore } from '../stores/auth';
	import { isOnline } from '../lib/stores/network';
	import { onMount } from 'svelte';
	import { validateSession } from '$lib/guards/auth';

	const navItems = [
		{ href: '/', label: 'Home', icon: '🏠' },
		{ href: '/upload', label: 'Upload', icon: '📤' },
		{ href: '/dashboard', label: 'DashBoard', icon: '📊' }
	];

	function isActive(href: string): boolean {
		if (href === '/') {
			return page.url.pathname === '/';
		}
		return page.url.pathname.startsWith(href);
	}

	let mobileMenuOpen = false;

	function toggleMobileMenu() {
		mobileMenuOpen = !mobileMenuOpen;
	}

	function closeMobileMenu() {
		mobileMenuOpen = false;
	}

	onMount(async () => {
		await validateSession();
	});
</script>

<div class="min-h-screen bg-gray-50">
	<!-- Offline banner -->
	{#if !$isOnline}
		<div class="bg-yellow-500 px-4 py-2 text-center text-sm font-medium text-white">
			⚠️ You're offline. Some features may not be available.
		</div>
	{/if}

	<nav class="border-b border-gray-200 bg-white shadow-sm">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="flex h-16 justify-between">
				<!-- Logo/Brand -->
				<div class="flex items-center">
					<button
						on:click={() => goto('/')}
						class="flex items-center space-x-2 text-xl font-bold text-gray-900 transition-colors hover:text-blue-600"
					>
						<span class="text-2xl">🎙️</span>
						<span>TTS Studio</span>
					</button>
				</div>

				<!-- Nav Links Desktop -->
				<div class="hidden items-center space-x-1 md:flex">
					{#each navItems as item (item.href)}
						<a href={item.href} class="nav-link">
							<span class="mr-2">{item.icon}</span>
							{item.label}
						</a>
					{/each}

					<!-- Auth Navigation -->
					{#if $authStore.isAuthenticated && $authStore.user}
						<a href="/profile" class="nav-link {isActive('/profile') ? 'nav-link-active' : ''}">
							<span class="mr-2">👤</span>
							Profile
						</a>
					{:else}
						<a href="/login" class="nav-link">
							<span class="mr-2">🔐</span>
							Login
						</a>
					{/if}
				</div>

				<!-- mobile menu button -->
				<div class="flex items-center md:hidden">
					<button
						on:click={toggleMobileMenu}
						class="rounded-md p-2 text-gray-600 hover:text-gray-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
						aria-label="Toggle menu"
					>
						{#if mobileMenuOpen}
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M6 18L18 6M6 6l12 12"
								/>
							</svg>
						{:else}
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M4 6h16M4 12h16M4 18h16"
								/>
							</svg>
						{/if}
					</button>
				</div>
			</div>
		</div>

		<!-- Mobile menu -->
		{#if mobileMenuOpen}
			<div class="border-t border-gray-200 md:hidden">
				<div class="space-y-1 px-2 pt-2 pb-3">
					{#each navItems as item (item.href)}
						<a
							href={item.href}
							on:click={closeMobileMenu}
							class="block rounded-md px-3 py-2 text-base font-medium {isActive(item.href)
								? 'bg-blue-100 text-blue-700'
								: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}"
						>
							<span class="mr-2">{item.icon}</span>
							{item.label}
						</a>
					{/each}

					{#if $authStore.isAuthenticated && $authStore.user}
						<a
							href="/profile"
							on:click={closeMobileMenu}
							class="block rounded-md px-3 py-2 text-base font-medium {isActive('/profile')
								? 'bg-blue-100 text-blue-700'
								: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}"
						>
							<span class="mr-2">👤</span>
							Profile
						</a>
					{:else}
						<a
							href="/login"
							on:click={closeMobileMenu}
							class="block rounded-md px-3 py-2 text-base font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900"
						>
							<span class="mr-2">🔐</span>
							Login
						</a>
					{/if}
				</div>
			</div>
		{/if}
	</nav>

	<!-- Main Content -->
	<main class="flex-1">
		<slot />
	</main>

	<!-- Footer -->
	<footer class="mt-auto border-t border-gray-200 bg-white">
		<div class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
			<div class="justify between flex items-center text-sm text-gray-600">
				<p>&copy; 2025 TTS Studio.</p>
				<div class="flex space-x-4">
					<a href="#" class="hover:text-gray-900">Privacy</a>
					<a href="#" class="hover:text-gray-900">Terms</a>
					<a href="#" class="hover:text-gray-900">Support</a>
				</div>
			</div>
		</div>
	</footer>
</div>
