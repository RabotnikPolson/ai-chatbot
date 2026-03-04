import useChatStore from '../../store/useChatStore';
import MessageList from './MessageList';
import InputBar from './InputBar';
import { Hash, PanelLeftOpen, PanelLeftClose } from 'lucide-react';

// ─── Chat Header ──────────────────────────────────────────────────────────────

interface ChatHeaderProps {
    onToggleSidebar: () => void;
    sidebarOpen: boolean;
}

function ChatHeader({ onToggleSidebar, sidebarOpen }: ChatHeaderProps) {
    const chats = useChatStore((s) => s.chats);
    const activeChatId = useChatStore((s) => s.activeChatId);

    const activeChat = chats.find((c) => c.id === activeChatId);

    return (
        <header className="flex items-center px-4 py-3.5 border-b border-[#1e1e1e] bg-[#111111]/70 backdrop-blur-md shrink-0 gap-3">
            {/* Sidebar toggle button — always visible in the header */}
            <button
                onClick={onToggleSidebar}
                title={sidebarOpen ? 'Свернуть панель' : 'Открыть панель'}
                className="p-1.5 rounded-lg text-[#444] hover:text-[#aaa] hover:bg-[#1e1e1e] transition-all duration-200 shrink-0"
            >
                {sidebarOpen
                    ? <PanelLeftClose size={17} />
                    : <PanelLeftOpen size={17} />
                }
            </button>

            {/* Centered chat title */}
            <div className="flex-1 flex items-center justify-center gap-2">
                {activeChat ? (
                    <>
                        <Hash size={14} className="text-[#555]" />
                        <h1 className="text-sm font-semibold text-[#cccccc] truncate max-w-[480px]">
                            {activeChat.title}
                        </h1>
                    </>
                ) : (
                    <h1 className="text-sm font-semibold text-[#444]">VibeChat</h1>
                )}
            </div>

            {/* Right spacer to keep title truly centered */}
            <div className="w-7 shrink-0" />
        </header>
    );
}

// ─── Chat Area ────────────────────────────────────────────────────────────────

interface ChatAreaProps {
    onToggleSidebar: () => void;
    sidebarOpen: boolean;
}

export default function ChatArea({ onToggleSidebar, sidebarOpen }: ChatAreaProps) {
    return (
        <div className="flex flex-col flex-1 h-full bg-[#0d0d0d] overflow-hidden">
            <ChatHeader onToggleSidebar={onToggleSidebar} sidebarOpen={sidebarOpen} />
            <MessageList />
            <InputBar />
        </div>
    );
}
