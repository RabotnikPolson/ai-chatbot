export interface User {
    id: number;
    email: string;
    role: 'admin' | 'user';
    created_at: string;
}

export interface Conversation {
    id: number;
    owner_user_id: number;
    title: string | null;
    created_at: string;
}

export type MessageStatus = 'queued' | 'processing' | 'done' | 'failed';
export type MessageRole = 'user' | 'assistant';

export interface Message {
    id: string;
    conversation_id: number;
    role: MessageRole;
    content: string;
    status: MessageStatus;
    provider?: string | null;
    latency_ms?: number | null;
    error?: string | null;
    created_at: string;
}

export interface AuthResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

export interface SendMessageRequest {
    text: string;
    temperature?: number;
}

export interface SendMessageResponse {
    message_id: string;
    status: MessageStatus;
}

export interface RegisterRequest {
    email: string;
    password: string;
}
