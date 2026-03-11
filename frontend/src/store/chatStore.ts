import { create } from 'zustand';

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
}

export const useChatStore = create<ChatState>((set) => ({
    conversations: [],
    activeConversationId: null,
    isLoading: false,
    setConversations: (conversations) => set({ conversations }),
    addConversation: (conversation) => set((state) => ({ conversations: [conversation, ...state.conversations] })),
    removeConversation: (id) => set((state) => ({ conversations: state.conversations.filter(c => c.id !== id) })),
    setActiveConversation: (id) => set({ activeConversationId: id }),
    setLoading: (isLoading) => set({ isLoading }),
}));
