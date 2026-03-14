<script lang="ts">
	import { goto } from '$app/navigation';

	const features = [
		{
			icon: '🎯',
			title: 'High Quality Synthesis',
			description: 'Convert text to natural sounding speech with advances AI models.'
		},
		{
			icon: '⚡',
			title: 'Fast Processing',
			description: 'Get your audio files generated quickly with our optimized pipeline.'
		},
		{
			icon: '🎨',
			title: 'Voice Customization',
			description: 'Choose from multiple voices and adjust speed, pitch, and tone.'
		},
		{
			icon: '📁',
			title: 'File Management',
			description: 'Organize and download your generated audio files easily.'
		}
	];
</script>

<svelte:head>
	<title>TTS Studio - Convert Text to Speech</title>
	<meta
		name="description"
		content="Professional text-to-speech conversion with high-quality AI voices."
	/>
</svelte:head>

<!-- Hero Section -->
<section class="bg-gradient-to-br from-blue-50 via-white to-purple-50">
	<div class="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
		<div class="text-center">
			<h1 class="lg:6xl mb-6 text-4xl font-bold text-gray-900 sm:text-5xl">
				Convert Text to
				<span class="to-purplr-600 bg-gradient-to-r from-blue-600 bg-clip-text text-transparent">
					Natural Speech
				</span>
			</h1>
			<p class="mx-auto mb-8 max-w-3xl text-xl text-gray-600">
				Transform your written content into professional-quality audio using advanced AI voice
				synthesis. Perfect for podcasts, audiobooks, presentations, and more.
			</p>

			<!-- CTA Buttons -->
			<div class="mb-4">
				<button onclick={() => goto('/upload')} class="btn-primary mb-4 px-8 py-3 text-lg">
					Start Converting
					<span class="ml-2">🚀</span>
				</button>
				<button onclick={() => goto('/dashboard')} class="btn-primary px-8 py-3 text-lg">
					View Dashboard
					<span class="ml-2">📊</span>
				</button>
			</div>

			<!-- Demo Preview -->
			<div class="card mx-auto max-w-2xl">
				<div class="mb-4 flex items-center space-x-4">
					<div class="h-3 w-3 rounded-full bg-red-500"></div>
					<div class="h-3 w-3 rounded-full bg-yellow-500"></div>
					<div class="h-3 w-3 rounded-full bg-green-500"></div>
					<span class="text-sm text-gray-500">Demo Preview</span>
				</div>
				<div class="rounded-lg bg-gray-100 p-4 text-left">
					<p class="mb-3 text-gray-700 italic">
						"Welcome to TTS Studio, where your text comes to life with natural-sounding voices..."
					</p>
					<div class="flex items-center space-x-3">
						<button
							class="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600 text-white hover:bg-blue-700"
						>
							▶️
						</button>
						<div class="h-2 flex-1 rounded-full bg-gray-300">
							<div class="h-2 w-1/3 rounded-full bg-blue-600"></div>
						</div>
						<span class="text-sm text-gray-500">0:15 / 0:45</span>
					</div>
				</div>
			</div>
		</div>
	</div>
</section>

<!-- Features Section -->
<section class="bg-white py-20">
	<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
		<div class="mb-16 text-center">
			<h2 class="mb-4 text-3xl font-bold text-gray-900">Powerful Features for Every Need</h2>
			<p class="mx-auto max-w-2xl text-lg text-gray-600">
				Everything you need to create professional audio content from text
			</p>
		</div>

		<div class="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
			{#each features as feature (feature.title)}
				<div class="card text-center transition-shadow hover:shadow-md">
					<div class="mb-4 text-4xl">{feature.icon}</div>
					<h3 class="mb-3 text-xl font-semibold text-gray-900">{feature.title}</h3>
					<p class="text-gray-600">{feature.description}</p>
				</div>
			{/each}
		</div>
	</div>
</section>

<!-- Stats Section -->
<section class="bg-gray-50 py-16">
	<div class="max-w-7xk mx-auto px-4 sm:px-6 lg:px-8">
		<div class="grid grid-cols-2 gap-8 text-center lg:grid-cols-4">
			<div>
				<div class="mb-2 text-3xl font-bold text-blue-600">50k+</div>
				<div class="text-gray-600">Texts Converted</div>
			</div>
			<div>
				<div class="mb-2 text-3xl font-bold text-green-600">25</div>
				<div class="text-gray-600">Voice Options</div>
			</div>
			<div>
				<div class="mb-2 text-3xl font-bold text-purple-600">99.9%</div>
				<div class="text-gray-600">Uptime</div>
			</div>
			<div>
				<div class="mb-2 text-3xl font-bold text-orange-600">5s</div>
				<div class="text-gray-600">Avg Processing</div>
			</div>
		</div>
	</div>
</section>
