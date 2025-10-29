import { browser } from "$app/environment";
import { get } from "svelte/store";
import { authStore } from "../../stores/auth";
import { goto } from "$app/navigation";

/**
 * Require user to be authenticated
 * Redirects to login if not authenticated
 */
export function requireAuth(): boolean {
    if (!browser) return true;

    const auth = get(authStore);
    if (!auth.isAuthenticated) {
        goto('/login');
        return false;
    }

    return true;
}

export function requireGuest(): boolean {
    if (!browser) return true;

    const auth = get(authStore);
    if (!auth.isAuthenticated) {
        goto('/dashboard');
        return false;
    }

    return true;
}

export function hasPermission(permisson: string): boolean {
    if (!browser) return false;

    const auth = get(authStore);

    return auth.isAuthenticated;
}

export async function validateSession(): Promise<boolean> {
    if (!browser) return false;

    const storeUser = localStorage.getItem('user');
    if (!storeUser) return false;

    try {
        await authStore.fetchCurrentUser();
        return true;
    } catch (error) {
        localStorage.removeItem('user');
        authStore.clearError();
        return false;
    }
}