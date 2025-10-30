import { browser } from "$app/environment";
import { writable } from "svelte/store";

export const isOnline = writable(browser ? navigator.onLine : true);

if (browser) {
    const updateOnlineStatus = () => {
        isOnline.set(navigator.onLine);
    };

    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);

    if (import.meta.hot) {
        import.meta.hot.dispose(() => {
            window.removeEventListener('online', updateOnlineStatus);
            window.removeEventListener('offline', updateOnlineStatus);
        });
    }
}