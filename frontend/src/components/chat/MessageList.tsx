import { useEffect, useRef } from 'react';
import useChatStore from '../../store/useChatStore';
import { MessageBubble } from './MessageBubble';
import { Sparkles } from 'lucide-react';

// ─── Empty State ──────────────────────────────────────────────────────────────

function EmptyState() {
    return (
        <div className="flex flex-col items-center justify-center h-full gap-4 select-none">
            <div className="relative">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#4f8ef7] to-[#7c3aed] flex items-center justify-center shadow-2xl shadow-blue-900/40">
                    <Sparkles size={28} className="text-white" />
                </div>
                <div className="absolute -inset-1 rounded-2xl bg-gradient-to-br from-[#4f8ef7] to-[#7c3aed] opacity-20 blur-md -z-10" />
            </div>
            <div className="text-center">
                <h2 className="text-xl font-semibold text-[#c0c0c0] mb-1">Начните разговор</h2>
                <p className="text-sm text-[#555] max-w-xs">
                    Задайте вопрос или попросите помочь с задачей
                </p>
            </div>
        </div>
    );
}

// ─── Message List ─────────────────────────────────────────────────────────────

export default function MessageList() {
    const messages = useChatStore((s) => s.messages);
    const activeChatId = useChatStore((s) => s.activeChatId);
    const bottomRef = useRef<HTMLDivElement>(null);

    // Auto-scroll on new messages
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    if (!activeChatId) {
        return <EmptyState />;
    }

    const chatMessages = messages.filter((m) => m.chatId === activeChatId);

    return (
        <div className="flex-1 overflow-y-auto px-4 py-6">
            <div className="max-w-3xl mx-auto space-y-6">
                {chatMessages.length === 0 ? (
                    <EmptyState />
                ) : (
                    chatMessages.map((msg) => (
                        <MessageBubble key={msg.id} message={msg} />
                    ))
                )}
                {/* Scroll anchor */}
                <div ref={bottomRef} />
            </div>
        </div>
    );
}
