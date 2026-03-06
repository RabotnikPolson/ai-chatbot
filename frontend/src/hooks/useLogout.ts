import { useNavigate } from 'react-router-dom';
import api from '../api/axiosInstance';
import useChatStore from '../store/useChatStore';

export function useLogout() {
    const navigate = useNavigate();
    const setUser = useChatStore((s) => s.setUser);
    const setAccessToken = useChatStore((s) => s.setAccessToken);
    const setChats = useChatStore((s) => s.setChats);
    const setMessages = useChatStore((s) => s.setMessages);
    const setActiveChatId = useChatStore((s) => s.setActiveChatId);
    const setWsStatus = useChatStore((s) => s.setWsStatus);

    return async () => {
        try {
            // Send logout request so backend kills the httpOnly refresh cookie
            await api.post('/auth/logout');
        } catch (e) {
            console.error('Logout error:', e);
        } finally {
            setUser(null);
            setAccessToken(null);
            setChats([]);
            setMessages([]);
            setActiveChatId(null);
            setWsStatus('disconnected');
            navigate('/auth', { replace: true });
        }
    };
}
