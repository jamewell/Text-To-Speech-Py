<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { authStore } from '../stores/auth';

	const navItems = [
		{ href: '/', label: 'Home', icon: '🏠'},
		{ href: '/upload', label: 'Upload', icon: '📤'},
		{ href: '/dashboard', label: 'DashBoard', icon: '📊'},
	];

	function isActive(href: string): boolean {
		if (href === '/') {
			return $page.url.pathname === '/';
		}
		return $page.url.pathname.startsWith(href);
	}

	let mobileMenuOpen = false;

	function toggleMobileMenu() {
		mobileMenuOpen = !mobileMenuOpen;
	}

	function closeMobileMenu() {
		mobileMenuOpen = false;
	}
	
</script>

<div class="min-h-screen bg-gray-50">
	<nav class="bg-white shadow-sm border-b border-gray-200">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="flex justify-between h-16">
				<!-- Logo/Brand -->
				<div class="flex items-center">
					<button
						on:click={() => goto('/')}
						class="flex items-center space-x-2 text-xl font-bold text-gray-900 hover:text-blue-600 transition-colors"
					>
						<span class="text-2xl">🎙️</span>
						<span>TTS Studio</span>
					</button>
				</div>

				<!-- Nav Links Desktop -->
				<div class="hidden md:flex items-center space-x-1">
					{#each navItems as item}
						<a 
							href="{item.href}"
							class="nav-link"
						>
							<span class="mr-2">{item.icon}</span>
							{item.label}
						</a>
					{/each}

					<!-- Auth Navigation -->
					{#if $authStore.isAuthenticated && $authStore.user}
						<a
							href="/profile" 
							class="nav-link {isActive('/profile') ? 'nav-link-active' : ''}"
						>
							<span class="mr-2">👤</span>
							Profile
						</a>
					{:else}
						<a 
							href="/login"
							class="nav-link"
						>
							<span class="mr-2">🔐</span>
							Login
						</a>
					{/if}
				</div>

				<!-- mobile menu button -->
				<div class="md:hidden flex items-center">
					<button 
						class="text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md p-2"
						aria-label="Toggle menu"
					>
						{#if mobileMenuOpen}
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						{:else}
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
							</svg>
						{/if}
					</button>
				</div>
			</div>
		</div>

		<!-- Mobile menu -->
		{#if mobileMenuOpen}
			<div class="md:hidden border-t border-gray-200">
				<div class="px-2 pt-2 pb-3 space-y-1">
					{#each navItems as item}
						<a 
							href="{item.href}"
							on:click={closeMobileMenu}
							class="block px-3 py-2 rounded-md text-base font-medium {isActive(item.href) ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}"
						>
							<span class="mr-2">{item.icon}</span>
							{item.label}
						</a>
					{/each}

					{#if $authStore.isAuthenticated && $authStore.user}
						<a
							href="/profile"
							on:click={closeMobileMenu}
							class="block px-3 py-2 rounded-md text-base font-medium {isActive('/profile') ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}"
						>
							<span class="mr-2">👤</span>
							Profile
						</a>
					{:else}
						<a 
							href="/login"
							on:click={closeMobileMenu}
							class="block px-3 py-2 rounded-md text-base font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900"
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
	 <footer class="bg-white border-t border-gray-200 mt-auto">
		<div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
			<div class="flex justify between items-center text-sm text-gray-600">
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
