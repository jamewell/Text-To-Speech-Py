<script lang="ts">
    import { authStore } from "../../stores/auth";
	import { goto } from "$app/navigation";
	import { onMount } from "svelte";
	import RegisterForm from "$lib/components/auth/RegisterForm.svelte";


    onMount(() => {
        if ($authStore.isAuthenticated) {
            goto('/dashboard');
        }
    });
</script>

<svelte:head>
    <title>Register - TTS Studio</title>
    <meta name="description" content="Create your TTS Studio account" />
</svelte:head>

<div class="min-h-[calc(100vh-8rem)] flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 px-4 py-12">
    <div class="max-w-md w-full">
        <!-- Header -->
        <div class="text-center mb-8">
            <div class="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-fulll mb-4">
                <span class="text-3xl">🎙️</span>
            </div>
            <h1 class="text-3xl font-bold text-gray-900 mb-2">
                Create Your Account
            </h1>
            <p class="text-gray-600">
                Join TTS Studio and start converting text to speech
            </p>
        </div>

        <!-- Register form card -->
        <div class="card">
            <RegisterForm />
        </div>

        <!-- Additional info -->
        <div class="mt-8 text-center">
            <p class="text-sm text-gray-500">
                By creating an account, you agree to our
				<a href="#" class="text-blue-600 hover:underline">Terms of Service</a>
				and
				<a href="#" class="text-blue-600 hover:underline">Privacy Policy</a>
            </p>
        </div>
    </div>
</div>