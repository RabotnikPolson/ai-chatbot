import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { Chat, Message, WsStatus, User } from '../types';
import { mockChats, mockMessages, mockUser } from '../data/mockData';

// ─── State + Actions ──────────────────────────────────────────────────────────

interface ChatStore {
    // State
    user: User | null;
    chats: Chat[];
    activeChatId: string | null;
    messages: Message[];
    wsStatus: WsStatus;

    // Actions
    setUser: (user: User | null) => void;
    setChats: (chats: Chat[]) => void;
    setActiveChatId: (id: string | null) => void;
    setMessages: (messages: Message[]) => void;
    setWsStatus: (status: WsStatus) => void;

    addChat: (chat: Chat) => void;
    removeChat: (id: string) => void;
    updateChat: (id: string, partial: Partial<Chat>) => void;

    addMessage: (message: Message) => void;

    /** Auto-generate chat title from first 3 words of the first user message */
    generateChatTitle: (firstMessage: string) => string;

    /** Load mock data (replace with real API calls later) */
    loadMockData: () => void;
}

const useChatStore = create<ChatStore>()(
    devtools(
        (set) => ({
            // ── Initial State ──────────────────────────────────────────────────────
            user: null,
            chats: [],
            activeChatId: null,
            messages: [],
            wsStatus: 'disconnected',

            // ── Setters ────────────────────────────────────────────────────────────
            setUser: (user) => set({ user }, false, 'setUser'),
            setChats: (chats) => set({ chats }, false, 'setChats'),
            setActiveChatId: (id) => set({ activeChatId: id }, false, 'setActiveChatId'),
            setMessages: (messages) => set({ messages }, false, 'setMessages'),
            setWsStatus: (status) => set({ wsStatus: status }, false, 'setWsStatus'),

            // ── Chat CRUD ──────────────────────────────────────────────────────────
            addChat: (chat) =>
                set((s) => ({ chats: [chat, ...s.chats] }), false, 'addChat'),

            removeChat: (id) =>
                set(
                    (s) => ({
                        chats: s.chats.filter((c) => c.id !== id),
                        activeChatId: s.activeChatId === id ? null : s.activeChatId,
                    }),
                    false,
                    'removeChat'
                ),

            updateChat: (id, partial) =>
                set(
                    (s) => ({
                        chats: s.chats.map((c) => (c.id === id ? { ...c, ...partial } : c)),
                    }),
                    false,
                    'updateChat'
                ),

            // ── Messages ───────────────────────────────────────────────────────────
            addMessage: (message) =>
                set((s) => ({ messages: [...s.messages, message] }), false, 'addMessage'),

            // ── Helpers ────────────────────────────────────────────────────────────
            generateChatTitle: (firstMessage: string) => {
                const words = firstMessage.trim().split(/\s+/).slice(0, 3);
                return words.join(' ');
            },

            // ── Mock Data ──────────────────────────────────────────────────────────
            loadMockData: () => {
                const firstChatId = mockChats[0]?.id ?? null;
                set(
                    {
                        user: mockUser,
                        chats: mockChats,
                        activeChatId: firstChatId,
                        messages: mockMessages,
                        wsStatus: 'connected',
                    },
                    false,
                    'loadMockData'
                );
            },
        }),
        { name: 'ChatStore' }
    )
);

export default useChatStore;
