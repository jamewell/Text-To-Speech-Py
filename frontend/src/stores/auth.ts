import { writable } from 'svelte/store';
import { goto } from '$app/navigation';
import { api, type ApiError } from '$lib/api';
import { browser } from '$app/environment';
import type { User, AuthResponse } from '$lib/schemas/api';

export interface AuthState {
	user: User | null;
	isAuthenticated: boolean;
	isLoading: boolean;
	error: string | null;
}

const initialState: AuthState = {
	user: null,
	isAuthenticated: false,
	isLoading: false,
	error: null
};

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>(initialState);

	// Load user from localStorage on inintialization
	if (browser) {
		const storedUser = localStorage.getItem('user');

		if (storedUser) {
			try {
				const user = JSON.parse(storedUser);
				set({
					user,
					isAuthenticated: true,
					isLoading: false,
					error: null
				});
			} catch {
				// Invalid stored data, clear it
				localStorage.removeItem('user');
			}
		}
	}

	function setAuthenticatedUser(user: User): void {
		if (browser) {
			localStorage.setItem('user', JSON.stringify(user));
		}

		set({
			user,
			isAuthenticated: true,
			isLoading: false,
			error: null
		});
	}

	function clearAuthState(): void {
		if (browser) {
			localStorage.removeItem('user');
		}

		set(initialState);
	}

	return {
		subscribe,

		async register(email: string, password: string): Promise<boolean> {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response: AuthResponse = await api.register(email, password);

				const user = response.user;

				setAuthenticatedUser(user);

				await goto('/dashboard');
				return true;
			} catch (error) {
				const apiError = error as ApiError;
				update((state) => ({
					...state,
					isLoading: false,
					error: apiError.message || 'Registration failed'
				}));
				return false;
			}
		},

		async login(email: string, password: string): Promise<boolean> {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response: AuthResponse = await api.login(email, password);

				const user = response.user;

				setAuthenticatedUser(user);

				await goto('/dashboard');
				return true;
			} catch (error) {
				const apiError = error as ApiError;
				update((state) => ({
					...state,
					isLoading: false,
					error: apiError.message || 'Login failed'
				}));
				return false;
			}
		},

		async logout(): Promise<void> {
			try {
				await api.logout();
			} catch (error) {
				console.error('Logout error: ', error);
			} finally {
				clearAuthState();
				await goto('/auth');
			}
		},

		async fetchCurrentUser(): Promise<void> {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const user = await api.getCurrentUser();

				if (browser) {
					localStorage.setItem('user', JSON.stringify(user));
				}

				update((state) => ({
					...state,
					user,
					isAuthenticated: true,
					isLoading: false,
					error: null
				}));
			} catch (error) {
				clearAuthState();

				const apiError = error as ApiError;
				if (apiError.isAuthError) {
					await goto('/login');
				}
			}
		},

		clearError(): void {
			update((state) => ({ ...state, error: null }));
		}
	};
}

export const authStore = createAuthStore();
