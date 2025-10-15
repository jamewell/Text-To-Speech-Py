<script lang="ts">
	import { onMount } from "svelte";
	import { authStore } from "../../../stores/auth";
	import PasswordInput from "./PasswordInput.svelte";
	import Button from "../ui/Button.svelte";


    let email = '';
    let password = '';
    let emailError = '';
    let passwordError = '';

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
    <PasswordInput
        id="password"
        label="Password"
        bind:value={password}
        error={passwordError}
        placeholder="Enter your password"
        autocomplete="current-password"
        disabled={$authStore.isLoading}
        onBlur={() => validatePassword(password)}
    />

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
    <Button
        type="submit"
        variant="primary"
        fullWidth={true}
        disabled={!isFormValid}
        loading={$authStore.isLoading}
        loadingText="Signing in..."
    >
        Sign in
    </Button>

    <!-- Additional Links -->
    <div class="text-center text-sm text-gray-600">
        Don't have an account
        <a href="/register" class="text-blue-600 hover:text-blue-700 font-medium">
            Sign up
        </a>
    </div>
</form>