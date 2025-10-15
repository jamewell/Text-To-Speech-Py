<script lang="ts">
    export let type: 'button' | 'submit' | 'reset' = 'button';
    export let variant: 'primary' | 'secondary' | 'danger' | 'ghost' = 'primary';
    export let size: 'sm' | 'md' | 'lg' = 'md';
    export let disabled: boolean = false;
    export let loading: boolean = false;
    export let fullWidth: boolean = false;
    export let loadingText: string = '';

    $: isDisabled = disabled || loading;

    const variantClasses = {
        primary: 'bg-blue-600 hover:bg-blue-700 text-white',
		secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-900',
		danger: 'bg-red-600 hover:bg-red-700 text-white',
		ghost: 'bg-transparent hover:bg-gray-100 text-gray-700 border border-gray-300'
    };

    const sizeClasses = {
        sm: 'py-1.5 px-3 text-sm',
		md: 'py-2 px-4 text-base',
		lg: 'py-3 px-6 text-lg'
    };

    $: buttonClasses = [
        'font-medium rounded-lg transition-colors duration-200',
        'flex items-center justify-center',
        'focus:outline-none focus:ring-2 focus:ring-offset-2',
        variant === 'primary' ? 'focus:ring-blue-500' : 'focus:ring-gray-500',
        variantClasses[variant],
        sizeClasses[size],
        fullWidth ? 'w-full' : '',
        isDisabled ? 'opacity-50 cursur-not-allowed' : 'cursor-pointer',
        $$props.class || ''
    ].filter(Boolean).join(' ')
</script>

<button
    {type}
    disabled={isDisabled}
    class={buttonClasses}
    on:click
>
    {#if loading}
		<svg class="animate-spin -ml-1 mr-3 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
			<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
			<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
		</svg>
		{#if loadingText}
			{loadingText}
		{:else}
			<slot name="loading">
				<slot />
			</slot>
		{/if}
	{:else}
		<slot />
	{/if}
</button>