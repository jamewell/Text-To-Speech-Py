import { config } from "./config";
import { z } from "zod";
import type { FileUploadResponse } from "./schemas/api";

const HTTP_STATUS_NO_CONTENT = 204;
const HTTP_STATUS_NETWORK_ERROR = 0;
const HTTP_STATUS_UNAUTHORIZED = 401;
const HTTP_STATUS_TIMEOUT = 408;

export interface ApiError {
    message: string;
    detail?: string;
    status: number;
    isNetworkError?: boolean;
    isTimeout?: boolean;
    isAuthError?: boolean;
    isValidationError?: boolean;
}

export class ApiValidationError extends Error {
    constructor(message: string, public errors: z.ZodError) {
        super(message);
        this.name = 'ApiValidationError';
    }
}

export class ApiClient {
    private baseUrl: string;
    private timeout: number;
    private maxRetries: number;
    private retryDelay: number;

    constructor(
        baseUrl: string = config.apiBaseUrl,
        timeout: number = config.requestTimeout,
        maxRetries: number = config.maxRetries,
        retryDelay: number = config.retryDelay,
    ) {
        this.baseUrl = baseUrl;
        this.timeout = timeout;
        this.maxRetries = maxRetries;
        this.retryDelay = retryDelay;
    }

    private async fetchWithTimeout(
        url: string,
        options: RequestInit = {}
    ): Promise<Response> {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
            });
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);

            if (error instanceof Error && error.name === 'AbortError') {
                throw {
                    message: 'Request timeout. Please check your connection and try again',
                    status: HTTP_STATUS_TIMEOUT,
                    isTimeout: true,
                } as ApiError;
            }
            throw error;
        }
    }

    private shouldRetry(error: ApiError, attempt: number): boolean {
        if (error.isAuthError || error.status === HTTP_STATUS_UNAUTHORIZED) {
            return false;
        }

        if (error.isValidationError) {
            return false;
        }

        if (attempt >= this.maxRetries) {
            return false;
        }

        return error.isNetworkError || (error.status >= 500 && error.status < 600);
    }

    /**
	 * Make an API request with runtime type validation
	 * @param endpoint API endpoint path
	 * @param options Fetch options
	 * @param schema Zod schema for response validation (optional)
	 * @param attempt Current retry attempt
	 * @returns Validated response data
	 */
    private async request<T>(
        endpoint: string,
        options: RequestInit = {},
        schema?: z.ZodType<T>,
        attempt: number = 1
    ): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;
        const isFormDataBody = options.body instanceof FormData;
        const headers: Record<string, string> = {};

        if (options.headers instanceof Headers) {
            options.headers.forEach((value, key) => {
                headers[key] = value;
            });
        } else if (Array.isArray(options.headers)) {
            for (const [key, value] of options.headers) {
                headers[key] = value;
            }
        } else if (options.headers) {
            Object.assign(headers, options.headers);
        }

        if (!isFormDataBody && !headers['Content-Type']) {
            headers['Content-Type'] = 'application/json';
        }

        try {
            const response = await this.fetchWithTimeout(url, {
                ...options,
                headers,
                credentials: 'include',
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const error: ApiError = {
                    message: errorData.detail || response.statusText || 'An error occurred',
                    detail: errorData.detail,
                    status: response.status,
                    isAuthError: response.status === HTTP_STATUS_UNAUTHORIZED
                }
                throw error;
            }

            if (response.status === HTTP_STATUS_NO_CONTENT) {
                return {} as T;
            }

            const data = await response.json();

            if (schema) {
                try {
                    return schema.parse(data);
                } catch (error) {
                    if (error instanceof z.ZodError) {
                        if (config.enableDebug) {
                            console.log('❌ API Response Validation Error:', {
                                endpoint,
                                error: error.message,
                                receivedData: data,
                            });
                        }

                        throw {
							message: 'Invalid response from server. Please try again or contact support.',
							detail: `Validation failed: ${error.message}`,
							status: response.status,
							isValidationError: true,
						} as ApiError;
                    }
                    throw error;
                }
            }

            if (config.enableDebug && !schema) {
                console.warn('⚠️ API request without schema validation:', endpoint);
            }

            return data as T;
        } catch (error) {
            if ((error as ApiError).status !== undefined) {
                const apiError = error as ApiError;

                if (this.shouldRetry(apiError, attempt)) {
                    await  new Promise(resolve => 
                        setTimeout(resolve, this.retryDelay * attempt)
                    );

                    if (config.enableDebug) {
                        console.log(`🔄 Retrying request (attempt ${attempt + 1}/${this.maxRetries}):`, endpoint);
                    }

                    return this.request<T>(endpoint, options, schema, attempt + 1);
                }

                throw apiError;
            }

            const networkError: ApiError = {
                message: 'Network error. Please check your connection.',
                status: HTTP_STATUS_NETWORK_ERROR,
                isNetworkError: true,
            };

            if (this.shouldRetry(networkError, attempt)) {
                await new Promise(resolve =>
                    setTimeout(resolve, this.retryDelay * attempt)
                );
                return this.request<T>(endpoint, options, schema, attempt + 1);
            }

            throw networkError;
        }

    }

    async register(email: string, password: string) {
        const { AuthResponseSchema } = await import('./schemas/api');

        return this.request(
            '/register', 
            {
                method: 'POST',
                body: JSON.stringify({email, password})
            },
            AuthResponseSchema
        );
    }

    async login(email: string, password: string) {
        const { AuthResponseSchema } = await import('./schemas/api');

        return this.request(
            '/login', 
            {
                method: 'POST',
                body: JSON.stringify({email, password})
            },
            AuthResponseSchema
        );
    }

    async logout() {
        const { LogoutResponseSchema } = await import('./schemas/api');

        return this.request(
            '/logout', 
            {
                method: 'POST',
            },
            LogoutResponseSchema,
        );
    }

    async getCurrentUser() {
        const { CurrentUserResponseSchema } = await import('./schemas/api');

        return this.request(
            '/me', 
            {
                method: 'GET',
            },
            CurrentUserResponseSchema,
        );
    }

    async refreshToken(refreshToken: string) {
        const { RefreshTokenResponseSchema } = await import('./schemas/api')

        return this.request(
            '/refresh',
            {
                method: 'POST',
                body: JSON.stringify({ refresh_token: refreshToken }),
            },
            RefreshTokenResponseSchema
        );
    }

    async uploadFile(file: File, onProgress?: (progress: number) => void): Promise<FileUploadResponse> {
        const { FileUploadResponseSchema } = await import('./schemas/api');
        const formData = new FormData();

        formData.append('file', file);
        const url = `${this.baseUrl}/files/upload_file`;

        return new Promise<FileUploadResponse>((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', url);
            xhr.withCredentials = true;
            xhr.timeout = this.timeout;

            xhr.upload.onprogress = (event) => {
                if (onProgress && event.lengthComputable) {
                    const progress = Math.round((event.loaded / event.total) * 100);
                    onProgress(progress);
                }
            };

            xhr.onload = () => {
                const rawResponse = xhr.responseText;
                let data: Record<string, unknown> = {};

                if (rawResponse) {
                    try {
                        data = JSON.parse(rawResponse) as Record<string, unknown>;
                    } catch {
                        data = {};
                    }
                }

                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        resolve(FileUploadResponseSchema.parse(data));
                    } catch (error) {
                        if (error instanceof z.ZodError) {
                            reject({
                                message: 'Invalid response from server. Please try again or contact support.',
                                detail: `Validation failed: ${error.message}`,
                                status: xhr.status,
                                isValidationError: true,
                            } as ApiError);
                            return;
                        }

                        reject(error);
                    }
                    return;
                }

                const detail = typeof data.detail === 'string' ? data.detail : undefined;
                reject({
                    message: detail || xhr.statusText || 'An error occurred',
                    detail,
                    status: xhr.status,
                    isAuthError: xhr.status === HTTP_STATUS_UNAUTHORIZED,
                } as ApiError);
            };

            xhr.onerror = () => {
                reject({
                    message: 'Network error. Please check your connection.',
                    status: HTTP_STATUS_NETWORK_ERROR,
                    isNetworkError: true,
                } as ApiError);
            };

            xhr.ontimeout = () => {
                reject({
                    message: 'Request timeout. Please check your connection and try again',
                    status: HTTP_STATUS_TIMEOUT,
                    isTimeout: true,
                } as ApiError);
            };

            xhr.send(formData);
        });
    }
}

export const api = new ApiClient();
