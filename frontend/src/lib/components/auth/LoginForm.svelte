<script lang="ts">
	import { onMount } from "svelte";
	import { authStore } from "../../../stores/auth";


    let email = '';
    let password = '';
    let emailError = '';
    let passwordError = '';
    let showPassword = false;

    $: isFormValid = email.length > 0 && password.length > 0;

    $: if (email) emailError = '';
    $: if (password) passwordError = '';

    onMount(() => {
        return () => {
            authStore.clearError();
        };
    });

    function validateEmail(value: string): boolean {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!value) {
            emailError = 'Email is required';
            return false;
        }

        if (!emailRegex.test(value)) {
            emailError = 'Please enter a valid email';
            return false;
        }

        emailError = '';
        return true;
    }

    function validatePassword(value: string): boolean {
        if (!value) {
            passwordError = 'Password is required';
            return false;
        }

        if (value.length < 8) {
            passwordError = 'Password must be at least 8 characters';
            return false;
        }

        passwordError = '';
        return true;
    }

    async function handleSubmit(event: Event) {
        event.preventDefault();

        const isValidEmail = validateEmail(email);
        const isValidPassword = validatePassword(password);

        if (!isValidEmail || isValidPassword) {
            return;
        }

        await authStore.login(email, password);
    }

    function togglePasswordVisibility() {
        showPassword = !showPassword;
    }
</script>

<form on:submit={handleSubmit} class="space-y-6">
    <!-- Email field -->
     <div>
        <label for="email" class="block text-sm font-medium text-gray-700 mb-2">
            Email
        </label>
        <input
            type="email"
            name="email" 
            id="email"
            bind:value={email}
            on:blur={() => validateEmail(email)}
            disabled={$authStore.isLoading}
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:right-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
            placeholder="you@example.com"
            autocomplete="email"
            required
        >
        {#if emailError}
            <p class="mt-1 test-sm text-red-600">{emailError}</p>
        {/if}
     </div>

     <!-- Password field -->
    <div>
        <label for="password" class="block text-sm font-medium text-gray-700 mb-2">
            Password
        </label>
        <div class="relative">
            <input 
                type={showPassword ? 'text' : 'password'} 
                name="password" 
                id="password"
                bind:value={password}
                on:blur={() => validatePassword(password)}
                disabled={$authStore.isLoading}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:right-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors pr-10"
                placeholder="Enter your password"
                autocomplete="current-password"
                required
            >
            <button 
                type="button"
                on:click={togglePasswordVisibility}
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 focus:outline-none"
                disabled={$authStore.isLoading}
                tabindex="-1"
            >
                {#if showPassword}
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
					</svg>
                {:else}
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
					</svg>
                {/if}
            </button>
        </div>
        {#if passwordError}
            <p class="mt-1 text-sm text-red-600">{passwordError}</p>
        {/if}
    </div>

    <!-- Error Message from api -->
    {#if $authStore.error}
        <div class="bg-red-50 border border-red-200 rounded-lg p-4">
            <div class="flex items-start">
                <span class="text-red-500 mr-3 text-xl">⚠️</span>
                <div>
                    <h3 class="text-sm font-medium text-red-800">Login Failed</h3>
                    <p class="text-sm text-red-700 mt-1">{$authStore.error}</p>
                </div>
            </div>
        </div>
    {/if}

    <!-- submit button -->
    <button 
        type="submit"
        disabled={!isFormValid || $authStore.isLoading}
        class="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
    >
        {#if $authStore.isLoading}
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Signing in...
        {:else}
            Sign In
        {/if}
    </button>

    <!-- Additional Links -->
    <div class="text-center text-sm text-gray-600">
        Don't have an account
        <a href="/register" class="text-blue-600 hover:text-blue-700 font-medium">
            Sign up
        </a>
    </div>
</form>