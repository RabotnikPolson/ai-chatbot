import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Conversation {
    id: number;
    title: string | null;
}

interface ChatState {
    conversations: Conversation[];
    activeConversationId: number | null;
    isLoading: boolean;
    setConversations: (conversations: Conversation[]) => void;
    addConversation: (conversation: Conversation) => void;
    removeConversation: (id: number) => void;
    setActiveConversation: (id: number | null) => void;
    setLoading: (isLoading: boolean) => void;
    clearState: () => void;
}

export const useChatStore = create<ChatState>()(
    persist(
        (set) => ({
            conversations: [],
            activeConversationId: null,
            isLoading: false,
            setConversations: (conversations) => set({ conversations }),
            addConversation: (conversation) => set((state) => ({ conversations: [conversation, ...state.conversations] })),
            removeConversation: (id) => set((state) => ({ conversations: state.conversations.filter(c => c.id !== id) })),
            setActiveConversation: (id) => set({ activeConversationId: id }),
            setLoading: (isLoading) => set({ isLoading }),
            clearState: () => {
                set({ conversations: [], activeConversationId: null, isLoading: false });
                localStorage.removeItem('chat-storage');
            },
        }),
        {
            name: 'chat-storage', // уникальное имя для ключа в localStorage
            partialize: (state) => ({ activeConversationId: state.activeConversationId }), // Сохраняем ТОЛЬКО айди активного чата
        }
    )
);
