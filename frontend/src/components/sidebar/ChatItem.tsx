import { useState } from 'react';
import { Trash2, X } from 'lucide-react';
import useChatStore from '../../store/useChatStore';
import type { Chat } from '../../types';

interface DeleteModalProps {
    chat: Chat;
    onClose: () => void;
}

function DeleteModal({ chat, onClose }: DeleteModalProps) {
    const removeChat = useChatStore((s) => s.removeChat);

    const handleDelete = () => {
        removeChat(chat.id);
        onClose();
    };

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center"
            onClick={onClose}
        >
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

            {/* Modal */}
            <div
                className="relative z-10 bg-[#1c1c1e] border border-[#2a2a2a] rounded-2xl p-6 w-80 shadow-2xl"
                onClick={(e) => e.stopPropagation()}
            >
                <button
                    onClick={onClose}
                    className="absolute top-3 right-3 text-[#555] hover:text-[#aaa] transition-colors"
                >
                    <X size={16} />
                </button>

                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 rounded-xl bg-[#3a1a1a]">
                        <Trash2 size={18} className="text-[#e05555]" />
                    </div>
                    <h3 className="font-semibold text-[#e8e8e8] text-base">Удалить чат?</h3>
                </div>

                <p className="text-[#777] text-sm mb-5 leading-relaxed">
                    Чат &ldquo;<span className="text-[#aaa] font-medium">{chat.title}</span>&rdquo; будет
                    удалён без возможности восстановления.
                </p>

                <div className="flex gap-2">
                    <button
                        onClick={onClose}
                        className="flex-1 py-2 rounded-xl border border-[#2a2a2a] text-[#888] hover:text-[#ccc] hover:border-[#3a3a3a] transition-all text-sm font-medium"
                    >
                        Отмена
                    </button>
                    <button
                        onClick={handleDelete}
                        className="flex-1 py-2 rounded-xl bg-[#7f3030] hover:bg-[#9b3d3d] text-white transition-all text-sm font-medium"
                    >
                        Удалить
                    </button>
                </div>
            </div>
        </div>
    );
}

// ─── Sidebar Chat Item ─────────────────────────────────────────────────────────

interface ChatItemProps {
    chat: Chat;
    isActive: boolean;
    onClick: () => void;
}

export function ChatItem({ chat, isActive, onClick }: ChatItemProps) {
    const [hovered, setHovered] = useState(false);
    const [showModal, setShowModal] = useState(false);

    return (
        <>
            <div
                onMouseEnter={() => setHovered(true)}
                onMouseLeave={() => setHovered(false)}
                onClick={onClick}
                className={`
          group relative flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer
          transition-all duration-150 select-none
          ${isActive
                        ? 'bg-[#252525] text-[#e8e8e8]'
                        : 'text-[#888] hover:bg-[#1e1e1e] hover:text-[#ccc]'
                    }
        `}
            >
                {/* Pulsing activity dot */}
                {chat.hasNewActivity && !isActive && (
                    <span className="relative flex h-2 w-2 shrink-0">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
                    </span>
                )}

                <span className="flex-1 truncate text-sm font-medium">{chat.title}</span>

                {/* Trash icon on hover */}
                {hovered && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            setShowModal(true);
                        }}
                        className="shrink-0 p-1 rounded-lg text-[#555] hover:text-[#e05555] hover:bg-[#2a1a1a] transition-all"
                    >
                        <Trash2 size={14} />
                    </button>
                )}
            </div>

            {showModal && (
                <DeleteModal chat={chat} onClose={() => setShowModal(false)} />
            )}
        </>
    );
}
