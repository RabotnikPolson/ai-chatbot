import { Plus, Wifi, WifiOff, Loader2 } from 'lucide-react';
import useChatStore from '../../store/useChatStore';
import { ChatItem } from './ChatItem';
import type { Chat } from '../../types';

// ─── WS Status Badge ──────────────────────────────────────────────────────────

function WsStatusDot() {
    const status = useChatStore((s) => s.wsStatus);
    if (status === 'connected')
        return <Wifi size={13} className="text-emerald-500" />;
    if (status === 'connecting')
        return <Loader2 size={13} className="text-yellow-500 animate-spin" />;
    return <WifiOff size={13} className="text-[#555]" />;
}

function WsStatusLabel() {
    const status = useChatStore((s) => s.wsStatus);
    if (status === 'connected') return <>Подключено</>;
    if (status === 'connecting') return <>Подключение...</>;
    return <>Не подключено</>;
}

// ─── Logo ─────────────────────────────────────────────────────────────────────

function Logo() {
    return (
        <div className="flex items-center gap-2.5 px-1">
            <div className="relative w-8 h-8 rounded-xl bg-gradient-to-br from-[#4f8ef7] to-[#7c3aed] flex items-center justify-center shadow-lg shadow-blue-900/30">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path
                        d="M8 2C4.68 2 2 4.68 2 8s2.68 6 6 6 6-2.68 6-6-2.68-6-6-6zm0 2.5c.83 0 1.5.67 1.5 1.5S8.83 7.5 8 7.5 6.5 6.83 6.5 6 7.17 4.5 8 4.5zm0 7c-1.25 0-2.36-.63-3.03-1.59.86-.47 1.91-.73 3.03-.73s2.17.26 3.03.73C10.36 10.87 9.25 11.5 8 11.5z"
                        fill="white"
                    />
                </svg>
            </div>
            <div>
                <p className="text-sm font-semibold text-[#e8e8e8] tracking-tight leading-none">NeuralChat</p>
                <p className="text-[10px] text-[#444] leading-tight mt-0.5">Local AI Assistant</p>
            </div>
        </div>
    );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────

export default function Sidebar() {
    // Use individual selectors to avoid new-object-reference infinite loop
    const user = useChatStore((s) => s.user);
    const chats = useChatStore((s) => s.chats);
    const activeChatId = useChatStore((s) => s.activeChatId);
    const setActiveChatId = useChatStore((s) => s.setActiveChatId);
    const addChat = useChatStore((s) => s.addChat);

    const handleNewChat = () => {
        const newChat: Chat = {
            id: `chat-${Date.now()}`,
            title: 'Новый чат',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            hasNewActivity: false,
        };
        addChat(newChat);
        setActiveChatId(newChat.id);
    };

    const userInitial = user?.email?.[0]?.toUpperCase() ?? '?';

    return (
        <aside className="flex flex-col w-64 shrink-0 h-full bg-[#111111] border-r border-[#1e1e1e]">
            {/* ── TOP: Logo + New Chat ──────────────────────────────────────────── */}
            <div className="px-3 pt-5 pb-4 flex flex-col gap-3">
                <Logo />

                <button
                    onClick={handleNewChat}
                    className="
            flex items-center justify-center gap-2 w-full py-2.5 rounded-xl
            bg-gradient-to-r from-[#1e3a5f] to-[#1a2f50]
            border border-[#2a4a70]
            text-[#7bb3ff] hover:text-white
            hover:from-[#2a4a70] hover:to-[#1e3a60]
            hover:border-[#4f8ef7]
            text-sm font-semibold
            transition-all duration-200
            shadow-md shadow-blue-900/20
          "
                >
                    <Plus size={16} strokeWidth={2.5} />
                    Новый чат
                </button>
            </div>

            <div className="mx-3 border-t border-[#1e1e1e] mb-2" />

            {/* ── CENTER: Scrollable Chat List ──────────────────────────────────── */}
            <nav className="flex-1 overflow-y-auto px-2 space-y-0.5 py-1">
                <p className="px-2 py-1 text-[10px] font-semibold uppercase tracking-widest text-[#444] mb-1">
                    Чаты
                </p>
                {chats.length === 0 ? (
                    <p className="px-3 py-4 text-[#444] text-xs text-center">Нет чатов</p>
                ) : (
                    chats.map((chat) => (
                        <ChatItem
                            key={chat.id}
                            chat={chat}
                            isActive={chat.id === activeChatId}
                            onClick={() => setActiveChatId(chat.id)}
                        />
                    ))
                )}
            </nav>

            <div className="mx-3 border-t border-[#1e1e1e] mt-2" />

            {/* ── BOTTOM: User Profile ──────────────────────────────────────────── */}
            <div className="px-3 py-4 flex items-center gap-2.5">
                {/* Avatar */}
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#4f8ef7] to-[#7c3aed] flex items-center justify-center text-white text-sm font-bold shrink-0">
                    {userInitial}
                </div>

                <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-[#ccc] truncate">{user?.email}</p>
                    <div className="flex items-center gap-1 mt-0.5">
                        <WsStatusDot />
                        <span className="text-[10px] text-[#555]">
                            <WsStatusLabel />
                        </span>
                    </div>
                </div>

                {/* Logout button */}
                <button
                    title="Выйти"
                    className="
            shrink-0 px-2.5 py-1.5 rounded-lg
            bg-[#2a1111] border border-[#3a1515]
            text-[#7f4040] hover:text-[#e05555]
            hover:bg-[#3a1515] hover:border-[#5a2020]
            text-xs font-medium
            transition-all duration-200
          "
                >
                    Выйти
                </button>
            </div>
        </aside>
    );
}
