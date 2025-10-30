<script lang="ts">
	import { goto } from "$app/navigation";
    import { authStore } from "../../stores/auth";
	import { onMount } from "svelte";


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

<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <!-- Header -->
    <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">
            👤 My Profile
        </h1>
        <p class="text-gray-600">
            Manage your account settings and preferences
        </p>
    </div>

    {#if $authStore.user}
        <div class="space-y-6">
            <!-- Account Information Card -->
            <div class="card">
                <div class="flex items-start justify-between mb-2">
                    <div>
                        <h2 class="text-xl font-semibold text-gray-900 mb-1">
                            Account Information
                        </h2>
                        <p class="text-sm text-gray-500">
                            Your personal account details
                        </p>
                    </div>
                    <div class="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                        <span class="text-2xl text-white font-bold">
                            {$authStore.user.email.charAt(0).toUpperCase()}
                        </span>
                    </div>
                </div>

                <div class="space-y-4">
                    <div class="flex items-center justify-between py-3 border-b border-gray-200">
                        <div>
                            <p class="text-sm font-medium text-gray-500">Email</p>
                            <p class="text-base text-gray-900 mt-1">{$authStore.user.email}</p>
                        </div>
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            ✓ Verified
                        </span>
                    </div>

                    <div class="flex items-center justify-between py-3 border-b border-gray-200">
                        <div>
                            <p class="text-sm font-medium text-gray-500">Member Since</p>
                            <p class="text-base text-gray-900 mt-1">
                                {formatDate($authStore.user.created_at)}
                            </p>
                        </div>
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            {getDaysSinceJoined($authStore.user.created_at)} days ago
                        </span>
                    </div>

                    <div class="flex items-center justify-between py-3 border-b border-gray-200">
                        <div>
                            <p class="text-sm font-medium text-gray-500">Account Status</p>
                            <p class="text-base text-gray-900 mt-1">
                                {$authStore.user.is_active ? 'Active' : 'Inactive'}
                            </p>
                        </div>
                        {#if $authStore.user.is_active}
                            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                Active
                            </span>
                        {:else}
                            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                Inactive
                            </span>
                        {/if}
                    </div>

                    <div class="flex items-center justify-between py-3">
                        <div>
                            <p class="text-sm font-medium text-gray-500">User Id</p>
                            <p class="text-base text-gray-900 mt-1">{$authStore.user.id}</p>
                        </div>
                    </div>
                    
                </div>
            </div>

            <!-- Usage Statistics -->
            <div class="card">
                <h2 class="text-xl font-semibold text-gray-900 mb-4">
                    📊 Usage Statistics
                </h2>
                <div class="grid md:grid-cols-3 gap-6">
                    <div class="text-center p-4 bg-blue-50 rounded-lg">
                        <div class="text-3xl font-bold text-blue-600 mb-2">0</div>
                        <p class="text-sm text-gray-600">Total Conversions</p>
                    </div>
                    <div class="text-center p-4 bg-blue-50 rounded-lg">
                        <div class="text-3xl font-bold text-blue-600 mb-2">0</div>
                        <p class="text-sm text-gray-600">Audio Files</p>
                    </div>
                    <div class="text-center p-4 bg-blue-50 rounded-lg">
                        <div class="text-3xl font-bold text-blue-600 mb-2">0</div>
                        <p class="text-sm text-gray-600">Storage Used</p>
                    </div>
                </div>
                <p class="text-sm text-gray-500 mt-4 text-center">
                    Statistics will be updated as you use the service
                </p>
            </div>

            <!-- Quick actions card -->
            <div class="card">
                <h2 class="text-xl font-semibold text-gray-900 mb-4">
                    ⚡ Quick Actions
                </h2>
                <div class="grid md:grid-cols-2 gap-4">
                    <a 
                        href="/upload"
                        class="flex items-center p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all group"
                    >
                        <span class="text-3xl mr-4">📤</span>
                        <div>
                            <h3 class="font-medium text-gray-900 group-hover:text-blue-600">
                                Upload Text
                            </h3>
                            <p class="text-sm text-gray-500">
                                Convert new text to speech
                            </p>
                        </div>
                    </a>
                    <a 
                        href="/dashboard"
                        class="flex items-center p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all group"
                    >
                        <span class="text-3xl mr-4">📊</span>
                        <div>
                            <h3 class="font-medium text-gray-900 group-hover:text-blue-600">
                                View Dashboard
                            </h3>
                            <p class="text-sm text-gray-500">
                                Manage your projects
                            </p>
                        </div>
                    </a>
                </div>
            </div>

            <!-- Account actions card -->
            <div class="card">
                <h2 class="text-xl font-semibold text-gray-900 mb-4">
                    Account Settings
                </h2>
                <div class="space-y-3">
                    <button
                        class="w-full flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left"
                    >
                        <div class="flex items-center">
                            <span class="text-2xl mr-4">🔑</span>
                            <div>
                                <h3 class="font-medium text-gray-900">Change Password</h3>
                                <p class="text-sm text-gray-500">Update your password</p>
                            </div>
                        </div>
                        <span class="text-gray-400">→</span>
                    </button>
                    
                    <button
                        class="w-full flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left"
                    >
                        <div class="flex items-center">
                            <span class="text-2xl mr-4">🔔</span>
                            <div>
                                <h3 class="font-medium text-gray-900">Notification</h3>
                                <p class="text-sm text-gray-500">Manage notification preferences</p>
                            </div>
                        </div>
                        <span class="text-gray-400">→</span>
                    </button>
                    
                    <button
                        on:click={handleLogout}
                        class="w-full flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left"
                    >
                        <div class="flex items-center">
                            <span class="text-2xl mr-4">🚪</span>
                            <div>
                                <h3 class="font-medium text-red-600 group-hover:text-red-700">
                                    Sign out
                                </h3>
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
        <div class="card text-center py-12">
			<svg class="animate-spin h-12 w-12 mx-auto text-blue-600 mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
			</svg>
			<p class="text-gray-600">Loading profile...</p>
		</div>
    {/if}
</div>