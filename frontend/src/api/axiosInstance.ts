import axios from 'axios';
import useChatStore from '../store/useChatStore';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
    withCredentials: true, // httpOnly cookie for Refresh Token
    headers: {
        'Content-Type': 'application/json',
    },
});

// ─── Request interceptor (attach Access Token from memory/localStorage) ───────
api.interceptors.request.use(
    (config) => {
        // Attach access token from memory store
        const token = useChatStore.getState().accessToken;
        if (token) config.headers.Authorization = `Bearer ${token}`;
        return config;
    },
    (error) => Promise.reject(error)
);

// ─── Response interceptor (handle 401 / token refresh) ────────────────────────
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        // TODO: implement silent token refresh on 401
        return Promise.reject(error);
    }
);

export default api;
