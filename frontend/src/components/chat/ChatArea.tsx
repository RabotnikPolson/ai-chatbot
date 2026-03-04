import useChatStore from '../../store/useChatStore';
import MessageList from './MessageList';
import InputBar from './InputBar';
import { Hash } from 'lucide-react';

// ─── Chat Header ──────────────────────────────────────────────────────────────

function ChatHeader() {
    const chats = useChatStore((s) => s.chats);
    const activeChatId = useChatStore((s) => s.activeChatId);

    const activeChat = chats.find((c) => c.id === activeChatId);

    return (
        <header className="flex items-center justify-center gap-2 px-4 py-3.5 border-b border-[#1e1e1e] bg-[#111111]/70 backdrop-blur-md shrink-0">
            {activeChat ? (
                <>
                    <Hash size={14} className="text-[#555]" />
                    <h1 className="text-sm font-semibold text-[#cccccc] truncate max-w-[480px]">
                        {activeChat.title}
                    </h1>
                </>
            ) : (
                <h1 className="text-sm font-semibold text-[#444]">NeuralChat</h1>
            )}
        </header>
    );
}

// ─── Chat Area ────────────────────────────────────────────────────────────────

export default function ChatArea() {
    return (
        <div className="flex flex-col flex-1 h-full bg-[#0d0d0d] overflow-hidden">
            <ChatHeader />
            <MessageList />
            <InputBar />
        </div>
    );
}
