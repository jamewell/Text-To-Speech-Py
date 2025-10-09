import { writable } from "svelte/store";
import { goto } from "$app/navigation";
import {api, type ApiError} from '$lib/api';
import { browser } from "$app/environment";

export interface User {
    id: string;
    email: string;
    created_at: string;
    is_active: boolean;
}

export interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;
    token: string | null;
}

const initialState: AuthState = {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
    token: null,
};

function createAuthStore() {
    const { subscribe, set, update } = writable<AuthState>(initialState);

    // Load user from localStorage on inintialization
    if (browser) {
        const storedUser = localStorage.getItem('user');
        const storedToken = localStorage.getItem('token');

        if (storedUser && storedToken) {
            try {
                const user = JSON.parse(storedUser);
                set({
                    user,
                    isAuthenticated: true,
                    isLoading: false,
                    error: null,
                    token: storedToken,
                });
            } catch (error) {
                // Invalid stored data, clear it
                localStorage.removeItem('user');
                localStorage.removeItem('token');
            }
        }
    }

    function setAuthenticatedUser(user: User, token: string = 'session'): void {
        if (browser) {
            localStorage.setItem('user', JSON.stringify(user));
            localStorage.setItem('token', token)
        }

        set({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
            token,
        });
    }

    function clearAuthState(): void {
        if (browser) {
			localStorage.removeItem('user');
			localStorage.removeItem('token');
		}

		set(initialState);
    }

    return {
        subscribe,

        async register(email: string, password: string): Promise<boolean> {
            update(state => ({ ...state, isLoading: true, error: null}));

            try {
                const response: any = await api.register(email, password);

                const user = response.user;
                const token = response.token || 'session';

                setAuthenticatedUser(user, token)

                await goto('/dashboard');
                return true;
            } catch (error) {
                const apiError = error as ApiError;
                update(state => ({
                    ...state,
                    isLoading: false,
                    error: apiError.message || 'Registration failed',
                }));
                return false;
            }
        },

        async login(email: string, password: string): Promise<boolean> {
            update(state => ({ ...state, isLoading: true, error: null }));

            try {
                const response: any = await api.login(email, password);

                const user = response.user;
                const token = response.token || 'session';

                setAuthenticatedUser(user, token)

                await goto('/dashboard');
                return true;
            } catch (error) {
                const apiError = error as ApiError;
                update(state => ({
                    ...state,
                    isLoading: false,
                    error: apiError.message || 'Login failed',
                }));
                return false;
            }
        },

        async logout(): Promise<void> {
            try {
                await api.logout();
            } catch (error) {
                console.error('Logout error: ', error)
            } finally {
                clearAuthState();
                await goto('/auth')
            }
        },

        async fetchCurrentUser(): Promise<void> {
            update(state => ({ ...state, isLoading: true, error: null}));

            try {
                const response: any = await api.getCurrentUser();
                const user = response;

                if (browser) {
                    localStorage.setItem('user', JSON.stringify(user));
                }

                update(state => ({
                    ...state,
                    user,
                    isAuthenticated: true,
                    isLoading: false,
                    error: null,
                }))
            } catch (error) {
                clearAuthState();
            }
        },

        clearError(): void {
            update(state => ({ ...state, error: null }));
        },
    };
}

export const authStore = createAuthStore()