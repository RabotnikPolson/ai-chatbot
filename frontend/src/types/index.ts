// ─── Core Types ───────────────────────────────────────────────────────────────

export interface User {
    id: string;
    email: string;
    name: string;
}

export type MessageRole = 'user' | 'assistant';

export interface Message {
    id: string;
    chatId: string;
    role: MessageRole;
    content: string;
    createdAt: string;
}

export interface Chat {
    id: string;
    title: string;
    createdAt: string;
    updatedAt: string;
    /** True if this chat was updated in the background (not currently active) */
    hasNewActivity?: boolean;
}

export type WsStatus = 'connected' | 'disconnected' | 'connecting';

// ─── Store Shape ──────────────────────────────────────────────────────────────

export interface ChatState {
    chats: Chat[];
    activeChatId: string | null;
    messages: Message[];
    wsStatus: WsStatus;
    user: User | null;
}
