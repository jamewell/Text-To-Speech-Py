import { get } from "svelte/store";
import { authStore } from "../stores/auth";

const API_BASE_URL = 'http://localhost:8000/api/v1';
const HTTP_STATUS_NO_CONTENT = 204;
const HTTP_STATUS_NETWORK_ERROR = 0;

export interface ApiError {
    message: string;
    detail?: string;
    status: number;
}

export class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;

        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...(options.headers as Record<string, string>),
        };

        const auth = get(authStore);
        if (auth.isAuthenticated && auth.token) {
            headers['Authorization'] = `Bearer ${auth.token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
                credentials: 'include',
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const error: ApiError = {
                    message: errorData.detail || response.statusText || 'An error has occurred',
                    detail: errorData.detail,
                    status: response.status,
                };
                throw error
            }

            if (response.status === HTTP_STATUS_NO_CONTENT) {
                return {} as T;
            }

            return await response.json();
        } catch (error) {
            if ((error as ApiError).status) {
                throw error;
            }
            throw {
                message: 'Network error. Please check your connection.',
                status: HTTP_STATUS_NETWORK_ERROR,
            } as ApiError;
        }
    }

    async register(email: string, password: string) {
        return this.request('/register', {
            method: 'POST',
            body: JSON.stringify({email, password})
        });
    }

    async login(email: string, password: string) {
        return this.request('/login', {
            method: 'POST',
            body: JSON.stringify({email, password})
        });
    }

    async logout() {
        return this.request('/logout', {
            method: 'POST',
        });
    }

    async getCurrentUser() {
        return this.request('/me', {
            method: 'GET',
        });
    }
}

export const api = new ApiClient();