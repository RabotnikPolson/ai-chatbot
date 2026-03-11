import React, { useEffect } from 'react';
import { useAuthStore } from '../store/authStore';
import { useChatStore } from '../store/chatStore';
import api from '../api/axios';
import { useQuery } from '@tanstack/react-query';

interface LayoutProps {
    children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
    const logout = useAuthStore((state) => state.logout);
    const {
        conversations,
        activeConversationId,
        setConversations,
        setActiveConversation,
        removeConversation,
        setLoading
    } = useChatStore();

    const { isLoading, data: fetchedConversations } = useQuery({
        queryKey: ['conversations'],
        queryFn: async () => {
            const response = await api.get('/conversations/');
            const data = Array.isArray(response.data) ? response.data : response.data.items || [];
            const sortedData = data.sort((a: any, b: any) => b.id - a.id);
            return sortedData;
        }
    });

    useEffect(() => {
        setLoading(isLoading);
    }, [isLoading, setLoading]);

    useEffect(() => {
        if (fetchedConversations) {
            setConversations(fetchedConversations);
        }
    }, [fetchedConversations, setConversations]);

    const handleDeleteChat = async (e: React.MouseEvent, id: number) => {
        e.stopPropagation();
        try {
            await api.delete(`/conversations/${id}`);
            removeConversation(id);
            if (activeConversationId === id) {
                setActiveConversation(null);
            }
        } catch (error) {
            console.error('Ошибка удаления чата:', error);
        }
    };

    return (
        <div className="h-screen flex text-gray-100 bg-[#131314]">
            {/* Сайдбар */}
            <div className="w-64 bg-[#1E1F22] flex flex-col border-r border-[#303030]">
                {/* Верх (статика) */}
                <div className="p-4 pt-6">
                    <button
                        onClick={() => setActiveConversation(null)}
                        className="flex items-center gap-2 bg-[#2D2E31] hover:bg-[#3D3E41] text-gray-200 text-sm font-medium py-2 px-4 rounded-full transition w-max mb-6"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        Новый чат
                    </button>
                </div>

                {/* Середина (динамика, скролл) */}
                <div className="flex-1 overflow-y-auto px-3 space-y-1 custom-scrollbar">
                    <div className="text-xs font-semibold text-gray-500 mb-2 pl-2">Недавние</div>
                    {conversations.length === 0 ? (
                        <div className="text-gray-500 text-sm p-2 text-center mt-2">
                            Нет чатов
                        </div>
                    ) : (
                        conversations.map((chat) => (
                            <div
                                key={chat.id}
                                onClick={() => setActiveConversation(chat.id)}
                                className={`group flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition text-sm ${activeConversationId === chat.id
                                    ? 'bg-[#2D2E31] text-gray-100 font-medium'
                                    : 'text-gray-300 hover:bg-[#2D2E31] hover:text-gray-100'
                                    }`}
                            >
                                <div className="flex items-center gap-3 truncate">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 shrink-0 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                                    </svg>
                                    <span className="truncate">{chat.title || 'Новый диалог'}</span>
                                </div>
                                <button
                                    onClick={(e) => handleDeleteChat(e, chat.id)}
                                    className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-400 p-1 rounded transition-colors"
                                    title="Удалить чат"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                </button>
                            </div>
                        ))
                    )}
                </div>

                {/* Низ (статика) */}
                <div className="p-3">
                    <button
                        onClick={logout}
                        className="w-full text-left text-gray-300 hover:text-white hover:bg-[#2D2E31] p-2 rounded-lg transition flex items-center gap-3 text-sm font-medium"
                    >
                        <div className="w-6 h-6 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center shrink-0">
                            <span className="text-xs font-bold font-sans text-white">A</span>
                        </div>
                        Выйти
                    </button>
                </div>
            </div>

            {/* Основная зона */}
            <div className="flex-1 flex flex-col relative h-full min-w-0">
                {children}
            </div>
        </div>
    );
};

export default Layout;
