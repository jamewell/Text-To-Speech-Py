<script lang="ts">
	import { onMount } from "svelte";
	import { authStore } from "../../../stores/auth";
	import PasswordInput from "./PasswordInput.svelte";
	import Button from "../ui/Button.svelte";


    let email = '';
    let password = '';
    let confimPassword = '';
    let emailError = '';
    let passwordError = '';
    let confimPasswordError = '';

    $: isFormValid = 
        email.length > 0 &&
        password.length > 0 &&
        confimPassword.length > 0 &&
        !emailError &&
        !passwordError &&
        !confimPasswordError;

    $: if (email) emailError = '';
    $: if (password) passwordError = '';
    $: if (confimPassword) confimPasswordError = '';

    onMount(() => {
        return () => {
            authStore.clearError();
        };
    });

    function validateEmail(value: string): boolean {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        emailError = '';

        if (!value) {
            emailError = 'Email is required';
            return false;
        }

        if (!emailRegex.test(value)) {
            emailError = 'Please enter a valid email';
            return false;
        }

        return true;
    }

    function validatePassword(value: string): boolean {
        passwordError = '';

        if (!value) {
            passwordError = 'Password is required';
            return false;
        }

        if (value.length < 8) {
            passwordError = 'Password must be atleast 8 characters long';
            return false;
        }

        if (!/[A-Z]/.test(value)) {
			passwordError = 'Password must contain at least one uppercase letter';
			return false;
		}

		if (!/[a-z]/.test(value)) {
			passwordError = 'Password must contain at least one lowercase letter';
			return false;
		}

		if (!/\d/.test(value)) {
			passwordError = 'Password must contain at least one number';
			return false;
		}

		if (!/[!@#$%^&*(),.?":{}|<>]/.test(value)) {
			passwordError = 'Password must contain at least one special character';
			return false;
		}

        return true;
    }

    function validateConfirmPassword(value: string): boolean {
        confimPasswordError = '';

        if (!value) {
            confimPasswordError = 'please confirm your password';
            return false;
        }

        if (value !== password) {
            confimPasswordError = 'Passwords do not match';
            return false;
        }

        return true;
    }

    async function handleSubmit(event: Event) {
        event.preventDefault();

        const isValidEmail = validateEmail(email);
        const isValidPassword = validatePassword(password);
        const isValidConfirm = validateConfirmPassword(confimPassword);

        if (!isValidEmail || !isValidPassword || !isValidConfirm) {
            return;
        }

        await authStore.register(email, password);
    }
</script>

<form on:submit={handleSubmit} class="space-y-6">
    <!-- Email field -->
    <div>
        <label for="email" class="block text-sm font-medium text-gray-700 mb-2">
            Email 
        </label>
        <input 
            id="email"
            type="email"
            bind:value={email}
            on:blur={() => validateEmail(email)}
            disabled={$authStore.isLoading}
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:cursor-not-allowed transition-colors"
            placeholder="you@example.com"
            autocomplete="email"
            required
        />
        {#if emailError}
            <p class="mt-1 text-sm text-red-600">
                {emailError}
            </p>
        {/if}
    </div>

    <!-- Password field -->
    <PasswordInput
        id="password"
        label="Password"
        bind:value={password}
        error={passwordError}
        placeholder="Create a strong password"
        autocomplete="new-password"
        disabled={$authStore.isLoading}
        showStrengthIndicator={true}
        showRequirements={true}
        onBlur={() => validatePassword(password)}
    />

    <!-- Confirm Password field -->
    <PasswordInput
        id="confirmPassword"
        label="Confirm password"
        bind:value={confimPassword}
        error={confimPasswordError}
        placeholder="Confirm your password"
        autocomplete="new-password"
        disabled={$authStore.isLoading}
        onBlur={() => validateConfirmPassword(confimPassword)}
    />

    <!-- Error message from API -->
    {#if $authStore.error}
        <div class="bg-red-50 border border-red-200 rounded-lg p-4">
            <div class="flex items-start">
                <span class="text-red-500 mr-3 text-xl">⚠️</span>
                <div>
                    <h3 class="text-sm font-medium text-red-800">Registration failed</h3>
                    <p class="text-sm text-red-700 mt-1">{$authStore.error}</p>
                </div>
            </div>
        </div>
    {/if}

    <!-- Submit Button -->
    <Button
        type="submit"
        variant="primary"
        fullWidth={true}
        disabled={!isFormValid}
        loading={$authStore.isLoading}
        loadingText="Creating account..."
    >
        Create Account
    </Button>

    <!-- Additional Links -->
    <div class="text-center text-sm text-gray-600">
        Already have an account?
        <a href="/login" class="text-blue-600 hover:text-blue-700 font-medium">
            Sign in
        </a>
    </div>
</form>