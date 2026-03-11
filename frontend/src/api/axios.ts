import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const api = axios.create({
    baseURL: 'http://localhost:8000/',
});

api.interceptors.request.use(
    (config) => {
        const token = useAuthStore.getState().token;
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

api.interceptors.response.use(
    (response) => {
        return response;
    },
    async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            const refreshToken = useAuthStore.getState().refreshToken;

            if (refreshToken) {
                try {
                    const response = await axios.post('http://localhost:8000/auth/refresh', null, {
                        headers: {
                            Authorization: `Bearer ${refreshToken}`
                        }
                    });

                    const newAccessToken = response.data.access_token;
                    // We only get a new access token usually, but check if refresh is returned
                    const newRefreshToken = response.data.refresh_token || refreshToken;

                    useAuthStore.getState().setTokens(newAccessToken, newRefreshToken);

                    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                    return api(originalRequest);
                } catch (refreshError) {
                    // Refresh token expired or invalid
                    useAuthStore.getState().logout();
                    return Promise.reject(refreshError);
                }
            } else {
                useAuthStore.getState().logout();
            }
        }

        return Promise.reject(error);
    }
);

export default api;
