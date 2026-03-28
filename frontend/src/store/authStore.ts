import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { useChatStore } from './chatStore';

interface AuthState {
    token: string | null;
    refreshToken: string | null;
    isAuthenticated: boolean;
    setTokens: (accessToken: string, refreshToken: string) => void;
    logout: () => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            token: null,
            refreshToken: null,
            isAuthenticated: false,
            setTokens: (accessToken, refreshToken) => 
                set({ token: accessToken, refreshToken, isAuthenticated: true }),
            logout: () => {
                set({ token: null, refreshToken: null, isAuthenticated: false });
                useChatStore.getState().clearState();
            },
        }),
        {
            name: 'auth-storage',
        }
    )
);
