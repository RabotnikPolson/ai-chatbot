import React, { useState, useRef, useEffect } from 'react';
import { useChatStore } from '../store/chatStore';
import { useAuthStore } from '../store/authStore';
import api from '../api/axios';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
// @ts-ignore
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';

interface Message {
    id: number;
    content: string;
    role: 'user' | 'assistant';
    status?: string;
}

const AI_ICON = (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-full h-full text-purple-400">
        <path fillRule="evenodd" d="M9.315 4.54a.75.75 0 011.37 0l1.284 3.012a.75.75 0 00.418.418l3.013 1.284a.75.75 0 010 1.37l-3.013 1.284a.75.75 0 00-.418.418l-1.284 3.013a.75.75 0 01-1.37 0l-1.284-3.013a.75.75 0 00-.418-.418l-3.013-1.284a.75.75 0 010-1.37l3.013-1.284a.75.75 0 00.418-.418l1.284-3.012zM16.5 14.25a.75.75 0 011.37 0l.642 1.506a.75.75 0 00.418.418l1.506.642a.75.75 0 010 1.37l-1.506.642a.75.75 0 00-.418.418l-.642 1.506a.75.75 0 01-1.37 0l-.642-1.506a.75.75 0 00-.418-.418l-1.506-.642a.75.75 0 010-1.37l1.506-.642a.75.75 0 00.418-.418l.642-1.506zM18.75 6.75a.75.75 0 00-1.37 0l-.258.604a.75.75 0 01-.418.418l-.604.258a.75.75 0 000 1.37l.604.258a.75.75 0 01.418.418l.258.604a.75.75 0 001.37 0l.258-.604a.75.75 0 01.418-.418l.604-.258a.75.75 0 000-1.37l-.604-.258a.75.75 0 01-.418-.418l-.258-.604z" clipRule="evenodd" />
    </svg>
);

const CodeBlock = ({ node, inline, className, children, ...props }: any) => {
    const match = /language-(\w+)/.exec(className || '');
    const [isCopied, setIsCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(String(children).replace(/\n$/, ''));
        setIsCopied(true);
        setTimeout(() => setIsCopied(false), 2000);
    };

    if (!inline && match) {
        return (
            <div className="flex flex-col w-full">
                <div className="flex items-center justify-between px-4 py-2 bg-[#2D2E31] text-[#a8a8a8] text-xs border-b border-[#333333]">
                    <span>{match[1]}</span>
                    <button
                        onClick={handleCopy}
                        className="hover:text-white transition-colors flex items-center gap-1 cursor-pointer"
                        title="Копировать код"
                    >
                        {isCopied ? (
                            <>
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 text-green-500">
                                    <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
                                </svg>
                                <span>Скопировано</span>
                            </>
                        ) : (
                            <>
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                                    <path d="M7 3.5A1.5 1.5 0 018.5 2h3.879a1.5 1.5 0 011.06.44l3.122 3.12A1.5 1.5 0 0117 6.622V12.5a1.5 1.5 0 01-1.5 1.5h-1v-3.379a3 3 0 00-.879-2.121L10.5 5.379A3 3 0 008.379 4.5H7v-1z" />
                                    <path d="M4.5 6A1.5 1.5 0 003 7.5v9A1.5 1.5 0 004.5 18h7a1.5 1.5 0 001.5-1.5v-5.879a1.5 1.5 0 00-.44-1.06L9.44 6.439A1.5 1.5 0 008.378 6H4.5z" />
                                </svg>
                                <span>Копировать</span>
                            </>
                        )}
                    </button>
                </div>
                <div className="p-4 overflow-x-auto">
                    <code className={className} {...props}>
                        {children}
                    </code>
                </div>
            </div>
        );
    }
    
    return (
        <code className={className} {...props}>
            {children}
        </code>
    );
};

const ChatPage: React.FC = () => {
    const { activeConversationId, conversations, addConversation, setActiveConversation } = useChatStore();
    const [inputText, setInputText] = useState('');
    const [messages, setMessages] = useState<Message[]>([]);
    const [isSending, setIsSending] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const currentChat = conversations.find((c) => c.id === activeConversationId);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const { data: fetchedMessages } = useQuery({
        queryKey: ['messages', activeConversationId],
        queryFn: async () => {
            if (activeConversationId === null) return [];
            const response = await api.get(`/conversations/${activeConversationId}/messages`);
            return response.data;
        },
        enabled: activeConversationId !== null,
    });

    // Ref для хранения активных стримов, чтобы можно было отменить их при смене чата
    const activeStreams = useRef<Map<number, AbortController>>(new Map());

    useEffect(() => {
        // Очищаем стримы ПРИ СМЕНЕ активного чата или unmount, чтобы не было гонок
        return () => {
            activeStreams.current.forEach(ctrl => ctrl.abort());
            activeStreams.current.clear();
        };
    }, [activeConversationId]);

    useEffect(() => {
        if (fetchedMessages) {
            setMessages(fetchedMessages);

            // Авто-реконнект к активным генерациям
            fetchedMessages.forEach((msg: Message) => {
                if (msg.role === 'assistant' && (msg.status === 'processing' || msg.status === 'queued') && activeConversationId !== null) {
                    if (!activeStreams.current.has(msg.id)) {
                        const controller = new AbortController();
                        activeStreams.current.set(msg.id, controller);

                        streamMessage(msg.id, activeConversationId, controller.signal).finally(() => {
                            activeStreams.current.delete(msg.id);
                        });
                    }
                }
            });

        } else if (activeConversationId === null) {
            setMessages([]);
        }
    }, [fetchedMessages, activeConversationId]);

    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInputText(e.target.value);
    };

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            const scrollHeight = textareaRef.current.scrollHeight;
            textareaRef.current.style.height = Math.min(scrollHeight, 200) + 'px';
            textareaRef.current.style.overflowY = scrollHeight > 200 ? 'auto' : 'hidden';
        }
    }, [inputText]);

    const streamMessage = async (messageId: number, chatId: number, signal?: AbortSignal) => {
        const token = useAuthStore.getState().token;
        try {
            const response = await fetch(`http://localhost:8000/messages/${messageId}/stream`, {
                headers: { Authorization: `Bearer ${token}` },
                signal
            });

            if (!response.body) return;

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                // { stream: true } спасает русские буквы от разрыва пополам!
                const decoded = decoder.decode(value, { stream: true });
                buffer += decoded;

                const parts = buffer.split('\n\n');
                // Последний элемент всегда оставляем в буфере, так как чанк мог оборваться на середине слова
                buffer = parts.pop() || "";

                for (const part of parts) {
                    if (part.startsWith('data: ')) {
                        const payload = part.replace('data: ', '');

                        if (payload === '[DONE]' || payload === '[ERROR]') {
                            // Когда стрим закончился, запрашиваем чистовую версию из БД
                            const resp = await api.get(`/conversations/${chatId}/messages`);
                            setMessages(resp.data);
                            return;
                        }

                        // Бэкенд теперь присылает ВЕСЬ сгенерированный текст целиком,
                        // поэтому просто заменяем content, а не склеиваем. Это спасает от дублей.
                        setMessages(prev => prev.map(msg => {
                            if (msg.id === messageId) {
                                let cleanPayload = payload;
                                if (payload.startsWith('"') && payload.endsWith('"')) {
                                    try {
                                        cleanPayload = JSON.parse(payload);
                                    } catch (e) {
                                        cleanPayload = payload.replace(/^"|"$/g, '').replace(/\\n/g, '\n');
                                    }
                                } else {
                                    cleanPayload = payload.replace(/^"|"$/g, '').replace(/\\n/g, '\n');
                                }

                                return { ...msg, content: cleanPayload };
                            }
                            return msg;
                        }));
                    }
                }
            }
        } catch (error) {
            if (error instanceof Error && error.name === 'AbortError') {
                console.log('Стрим прерван при переключении чата');
            } else {
                console.error("Ошибка стриминга:", error);
            }
        }
    };

    const handleRetry = async (failedMsg: Message) => {
        if (!activeConversationId || isSending) return;
        setIsSending(true);
        try {
            // Find the previous user message that caused this failure
            const msgIndex = messages.findIndex(m => m.id === failedMsg.id);
            if (msgIndex <= 0) return;
            
            const prevUserMsg = messages[msgIndex - 1];
            if (prevUserMsg.role !== 'user') return;

            // Retrying means sending the text again
            await api.post(`/conversations/${activeConversationId}/messages`, {
                text: prevUserMsg.content
            });

            // Refetch messages and trigger stream
            const resp = await api.get(`/conversations/${activeConversationId}/messages`);
            const data = resp.data;
            setMessages(data);

            const lastAssistantMsg = data.slice().reverse().find((m: Message) => m.role === 'assistant');
            if (lastAssistantMsg && lastAssistantMsg.status !== 'done') {
                streamMessage(lastAssistantMsg.id, activeConversationId);
            }
        } catch (error) {
            console.error('Ошибка при повторе сообщения:', error);
        } finally {
            setIsSending(false);
        }
    };

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputText.trim() || isSending) return;

        const text = inputText;
        setInputText('');
        if (textareaRef.current) textareaRef.current.style.height = 'auto';
        setIsSending(true);

        try {
            let targetChatId = activeConversationId;

            if (targetChatId === null) {
                const title = text.split(' ').slice(0, 4).join(' ') || 'Новый чат';
                const response = await api.post('/conversations/', { title });
                targetChatId = response.data.id;

                addConversation(response.data);
                setActiveConversation(targetChatId);
            }

            setMessages(prev => [...prev, { id: Date.now(), content: text, role: 'user' }]);

            await api.post(`/conversations/${targetChatId}/messages`, {
                text: text
            });

            const resp = await api.get(`/conversations/${targetChatId}/messages`);
            const data = resp.data;
            setMessages(data);

            // Обработка SSE стриминга
            const lastAssistantMsg = data.slice().reverse().find((m: Message) => m.role === 'assistant');
            if (lastAssistantMsg && lastAssistantMsg.status !== 'done' && targetChatId !== null) {
                streamMessage(lastAssistantMsg.id, targetChatId);
            }

        } catch (error) {
            console.error('Ошибка отправки сообщения:', error);
        } finally {
            setIsSending(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-[#131314]">
            {/* Шапка чата */}
            <div className="p-4 flex items-center justify-between shadow-sm z-10">
                <div className="flex items-center gap-3">
                    <h2 className="text-lg font-medium text-gray-200">
                        {activeConversationId === null ? 'VibeChat' : (currentChat?.title || 'Диалог без названия')}
                    </h2>
                </div>
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center shrink-0 cursor-pointer hover:opacity-90">
                        <span className="text-sm font-bold text-white">A</span>
                    </div>
                </div>
            </div>

            {/* Зона сообщений */}
            <div className="flex-1 overflow-y-auto px-4 lg:px-48 xl:px-64 pt-6 space-y-8 flex flex-col pb-4 custom-scrollbar">
                {activeConversationId === null && messages.length === 0 ? (
                    <div className="flex-1 flex flex-col items-center justify-center text-center px-4 mt-20">
                        <div className="w-16 h-16 mb-6 opacity-80">
                            {AI_ICON}
                        </div>
                        <h1 className="text-3xl font-medium text-gray-200 mb-2">Чем я могу помочь?</h1>
                        <p className="text-[#a8a8a8] max-w-md">Я локальный AI чат-бот. Напишите ваш вопрос ниже, чтобы начать общение.</p>
                    </div>
                ) : (
                    messages.map((msg) => (
                        msg.role === 'user' ? (
                            <div key={msg.id} className="flex justify-end w-full">
                                <div className="bg-[#2A2B2E] text-[#e3e3e3] rounded-3xl px-6 py-3 max-w-[80%] text-[15px] leading-relaxed shadow-sm">
                                    <div className="prose prose-invert max-w-none break-words">
                                        <ReactMarkdown 
                                            remarkPlugins={[remarkGfm]} 
                                            rehypePlugins={[rehypeHighlight]}
                                            components={{
                                                code: CodeBlock
                                            }}
                                        >
                                            {msg.content}
                                        </ReactMarkdown>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div key={msg.id} className="flex justify-start w-full gap-4">
                                <div className="shrink-0 w-8 h-8 mt-1">
                                    {AI_ICON}
                                </div>
                                <div className="text-[#e3e3e3] text-[15px] leading-relaxed max-w-[85%] mt-1 overflow-hidden flex flex-col gap-2">
                                    <div className="prose prose-invert max-w-none break-words overflow-x-auto">
                                        <ReactMarkdown 
                                            remarkPlugins={[remarkGfm]} 
                                            rehypePlugins={[rehypeHighlight]}
                                            components={{
                                                code: CodeBlock
                                            }}
                                        >
                                            {msg.content || (msg.status === 'failed' ? 'Произошла ошибка при генерации ответа.' : 'Ожидание ответа...')}
                                        </ReactMarkdown>
                                    </div>
                                    
                                    {/* Индикаторы статусов */}
                                    <div className="flex items-center gap-2 mt-1">
                                        {msg.status === 'queued' && (
                                            <span className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded-full flex items-center gap-1 w-max">
                                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                </svg>
                                                В очереди...
                                            </span>
                                        )}
                                        {msg.status === 'processing' && (
                                            <span className="text-xs bg-blue-900/50 text-blue-300 px-2 py-0.5 rounded-full flex items-center gap-1 w-max">
                                                <svg className="animate-spin w-3 h-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                </svg>
                                                Генерация...
                                            </span>
                                        )}
                                        {msg.status === 'failed' && (
                                            <div className="flex items-center gap-2">
                                                <span className="text-xs bg-red-900/50 text-red-300 px-2 py-0.5 rounded-full flex items-center gap-1 w-max">
                                                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                    </svg>
                                                    Ошибка
                                                </span>
                                                <button 
                                                    onClick={() => handleRetry(msg)}
                                                    className="text-xs bg-[#2D2E31] hover:bg-[#3D3E41] text-gray-200 px-3 py-1 rounded-full flex items-center gap-1 transition-colors"
                                                >
                                                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                                    </svg>
                                                    Повторить
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Зона ввода */}
            <div className="px-4 lg:px-48 xl:px-64 pb-6 pt-2">
                <form onSubmit={handleSendMessage} className="relative">
                    <div className="bg-[#1E1F22] rounded-[32px] pt-1 pb-1 px-1 flex flex-col relative border border-transparent focus-within:bg-[#202124] focus-within:border-gray-700 transition-all duration-300">

                        <div className="px-4 py-3 w-full flex-1 min-h-[50px]">
                            <textarea
                                ref={textareaRef}
                                className="w-full bg-transparent text-[#e3e3e3] placeholder-gray-500 focus:outline-none resize-none leading-relaxed text-[16px] custom-scrollbar block max-h-[200px]"
                                placeholder="Введите текст здесь"
                                rows={1}
                                value={inputText}
                                onChange={handleInput}
                                disabled={isSending}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        handleSendMessage(e);
                                    }
                                }}
                            />
                        </div>

                        <div className="flex items-center justify-end px-2 pb-1">
                            <div className="flex items-center gap-2 pr-1">
                                <button
                                    type="submit"
                                    disabled={!inputText.trim() || isSending}
                                    className={`ml-1 p-2 rounded-full transition-colors flex items-center justify-center ${inputText.trim() && !isSending ? 'bg-[#ECECEC] text-[#131314] hover:bg-[#FFFFFF]' : 'bg-[#131314] text-[#808080]'}`}
                                >
                                    {isSending ? (
                                        <svg className="animate-spin h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                    ) : (
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                                        </svg>
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                    <div className="text-center mt-3">
                        <span className="text-[11px] text-[#A8A8A8]">
                            VibeChat – это ИИ. Он может ошибаться. Проверяйте важную информацию.
                        </span>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default ChatPage;
