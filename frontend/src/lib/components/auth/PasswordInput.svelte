<script lang="ts">
    export let id: string;
    export let label: string;
    export let value: string = '';
    export let error: string = '';
    export let placeholder: string = 'Enter password';
    export let autocomplete: string = 'current-password';
    export let disabled: boolean = false;
    export let showStrengthIndicator: boolean = false;
    export let showRequirements: boolean = false;
    export let onBlur: (() => void) | undefined = undefined;

    let showPassword = false;

    function togglePasswordVisibility() {
        showPassword = !showPassword
    }

    $: passwordStrength = (() => {
        if (!value || !showStrengthIndicator) return { score: 0, label: '', color: ''};

        let score = 0;
        if (value.length >= 8) score++;
        if (/[A-Z]/.test(value)) score++;
        if (/[a-z]/.test(value)) score++;
        if (/\d/.test(value)) score++;
        if (/[!@#$%^&*(),.?":{}|<>]/.test(value)) score++;

        if (score <= 2) return { score, label: 'Weak', color: 'bg-red-500' };
        if (score <= 4) return { score, label: 'Meduim', color: 'bg-yellow-500' };
        return { score, label: 'Strong', color: 'bg-green-500' };
    })();
</script>

<div>
    <label for="{id}" class="block text-sm font-medium text-gray-700 mb-2">
        {label}
    </label>
    <div class="relative">
        <input
            {id}
            type={showPassword ? 'text' : 'password'}
            bind:value
            on:blur={onBlur}
            {disabled}
            {placeholder}
            {autocomplete}
            class="w-full px-4 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
            required
        />
        <button
            type="button"
            on:click={togglePasswordVisibility}
            class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 focus:outline-none"
            {disabled}
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

    <!-- Password Strength Indicator -->
    {#if showStrengthIndicator && value}
        <div class="mt-2">
            <div class="flex items-center gap-2">
                <div class="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                        class="h-2 rounded-full transition-all {passwordStrength.color}"
                        style="width: {(passwordStrength.score / 5) * 100}%"
                    ></div>
                </div>
                <span class="text-xs font-medium text-gray-600">
                    {passwordStrength.label}
                </span>
            </div>
        </div>
    {/if}

    {#if error}
        <p class="mt-1 text-sm text-red-600">{error}</p>
    {:else if showRequirements && value}
        <p class="mt-1 text-xs text-gray-500">
            Must be 8+ characters with uppercase, lowercase, number, and special character
        </p>
    {/if}
</div>