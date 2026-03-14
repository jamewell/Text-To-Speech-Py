export const config = {
	// API Configuration
	apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',

	// Environment
	environment: import.meta.env.MODE as 'development' | 'production' | 'testing',
	isDevelopment: import.meta.env.DEV,
	isProduction: import.meta.env.PROD,

	// Feature flags
	enableDebug: import.meta.env.VITE_ENABLE_DEBUG === 'true' || import.meta.env.DEV,
	enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',

	// Request Configuration
	requestTimeout: parseInt(import.meta.env.VITE_REQUEST_TIMEOUT || '30000'),
	maxRetries: parseInt(import.meta.env.VITE_MAX_RETRIES || '3'),
	retryDelay: parseInt(import.meta.env.VITE_RETRY_DELAY || '1000')
} as const;

// Validate required configuration
if (!config.apiBaseUrl) {
	throw new Error('VITE_API_BASE_URL is required');
}

// Log configuration in development
if (config.isDevelopment && config.enableDebug) {
	console.log('📋 App Configuration:', {
		apiBaseUrl: config.apiBaseUrl,
		environment: config.environment,
		isDevelopment: config.isDevelopment
	});
}
