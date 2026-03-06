import { useRef, useState, type KeyboardEvent } from 'react';
import { SendHorizonal } from 'lucide-react';
import useChatStore from '../../store/useChatStore';
import type { Message } from '../../types';

export default function InputBar() {
    const [text, setText] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const activeChatId = useChatStore((s) => s.activeChatId);

    const autoResize = () => {
        const ta = textareaRef.current;
        if (!ta) return;
        ta.style.height = 'auto';
        ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`;
    };

    const handleSend = () => {
        const trimmed = text.trim();
        if (!trimmed) return;

        let targetChatId = activeChatId;
        const store = useChatStore.getState();

        // 1. If there's no active chat, create one!
        if (!targetChatId) {
            targetChatId = `chat-${Date.now()}`;
            const newChat = {
                id: targetChatId,
                title: store.generateChatTitle(trimmed),
                updatedAt: new Date().toISOString(),
                createdAt: new Date().toISOString(),
            };
            store.addChat(newChat);
            store.setActiveChatId(targetChatId);
        } else {
            // 2. Only rename existing chat if it's explicitly "Новый чат"
            const chat = store.chats.find(c => c.id === targetChatId);
            if (chat && chat.title === 'Новый чат') {
                store.updateChat(targetChatId, {
                    title: store.generateChatTitle(trimmed),
                    updatedAt: new Date().toISOString(),
                });
            }
        }

        // 3. Add the message
        const newMsg: Message = {
            id: `msg-${Date.now()}`,
            chatId: targetChatId,
            role: 'user',
            content: trimmed,
            createdAt: new Date().toISOString(),
        };

        store.addMessage(newMsg);

        setText('');
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const canSend = text.trim().length > 0;

    return (
        <div className="px-4 pb-5 pt-3">
            <div className="max-w-3xl mx-auto">
                {/* Input container */}
                <div
                    className="
            flex items-end gap-3 px-4 py-3 rounded-2xl
            bg-[#1a1a1a] border border-[#2a2a2a]
            focus-within:border-[#3a3a3a] focus-within:shadow-lg focus-within:shadow-black/30
            transition-all duration-200
          "
                >
                    <textarea
                        ref={textareaRef}
                        value={text}
                        onChange={(e) => {
                            setText(e.target.value);
                            autoResize();
                        }}
                        onKeyDown={handleKeyDown}
                        placeholder="Введите сообщение..."
                        rows={1}
                        className="input-area disabled:opacity-40 disabled:cursor-not-allowed"
                    />

                    <button
                        onClick={handleSend}
                        disabled={!canSend}
                        className={`
              shrink-0 w-9 h-9 rounded-xl flex items-center justify-center mb-0.5
              transition-all duration-200
              ${canSend
                                ? 'bg-gradient-to-br from-[#4f8ef7] to-[#7c3aed] text-white shadow-md shadow-blue-900/40 hover:scale-105 hover:shadow-blue-700/50'
                                : 'bg-[#252525] text-[#444] cursor-not-allowed'
                            }
            `}
                    >
                        <SendHorizonal size={16} strokeWidth={2} />
                    </button>
                </div>

                <p className="text-center text-[10px] text-[#333] mt-2">
                    Enter — отправить &nbsp;·&nbsp; Shift+Enter — новая строка
                </p>
            </div>
        </div>
    );
}
