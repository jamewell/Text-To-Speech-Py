<script lang="ts">
    import { goto } from "$app/navigation";

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
        },
    ]
</script>

<svelte:head>
    <title>TTS Studio - Convert Text to Speech</title>
	<meta name="description" content="Professional text-to-speech conversion with high-quality AI voices." />
</svelte:head>

<!-- Hero Section -->
 <section class="bg-gradient-to-br from-blue-50 via-white to-purple-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div class="text-center">
            <h1 class="text-4xl sm:text-5xl lg:6xl font-bold text-gray-900 mb-6">
                Convert Text to
                <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purplr-600">
                    Natural Speech
                </span>
            </h1>
            <p class="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
                Transform your written content into professional-quality audio using advanced AI voice synthesis. 
				Perfect for podcasts, audiobooks, presentations, and more.
            </p>

            <!-- CTA Buttons -->
            <div class="mb-4">
                <button
                    onclick={() => goto('/upload')}
                    class="btn-primary text-lg px-8 py-3 mb-4"
                >
                    Start Converting
                    <span class="ml-2">🚀</span>
                </button>
                <button
                    onclick={() => goto('/dashboard')}
                    class="btn-primary text-lg px-8 py-3"
                >
                    View Dashboard
                    <span class="ml-2">📊</span>
                </button>
            </div>

             <!-- Demo Preview -->
            <div class="card max-w-2xl mx-auto">
                <div class="flex items-center space-x-4 mb-4">
                    <div class="w-3 h-3 bg-red-500 rounded-full"></div>
                    <div class="w-3 h-3 bg-yellow-500 rounded-full"></div>
                    <div class="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span class="text-gray-500 text-sm">Demo Preview</span>
                </div>
                <div class="bg-gray-100 rounded-lg p-4 text-left">
                    <p class="text-gray-700 italic mb-3">
                        "Welcome to TTS Studio, where your text comes to life with natural-sounding voices..."
                    </p>
                    <div class="flex items-center space-x-3">
						<button class="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white hover:bg-blue-700">
							▶️
						</button>
						<div class="flex-1 bg-gray-300 rounded-full h-2">
							<div class="bg-blue-600 h-2 rounded-full w-1/3"></div>
						</div>
						<span class="text-sm text-gray-500">0:15 / 0:45</span>
					</div>
                </div>
            </div>
        </div>
    </div>
 </section>

 <!-- Features Section -->
<section class="py-20 bg-white">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
            <h2 class="text-3xl font-bold text-gray-900 mb-4">
                Powerful Features for Every Need
            </h2>
            <p class="text-lg text-gray-600 max-w-2xl mx-auto">
                Everything you need to create professional audio content from text
            </p>
        </div>

        <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {#each features as feature}
                <div class="card text-center hover:shadow-md transition-shadow">
                    <div class="text-4xl mb-4">{feature.icon}</div>
                    <h3 class="text-xl font-semibold text-gray-900 mb-3">{feature.title}</h3>
                    <p class="text-gray-600">{feature.description}</p>
                </div>
            {/each}
        </div>
    </div>
</section>

<!-- Stats Section -->
<section class="py-16 bg-gray-50">
    <div class="max-w-7xk mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
            <div>
                <div class="text-3xl font-bold text-blue-600 mb-2">50k+</div>
                <div class="text-gray-600">Texts Converted</div>
            </div>
            <div>
                <div class="text-3xl font-bold text-green-600 mb-2">25</div>
                <div class="text-gray-600">Voice Options</div>
            </div>
            <div>
                <div class="text-3xl font-bold text-purple-600 mb-2">99.9%</div>
                <div class="text-gray-600">Uptime</div>
            </div>
            <div>
                <div class="text-3xl font-bold text-orange-600 mb-2">5s</div>
                <div class="text-gray-600">Avg Processing</div>
            </div>
        </div>
    </div>
</section>
