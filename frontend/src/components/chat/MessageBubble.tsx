import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import type { Message } from '../../types';
import { Bot, User } from 'lucide-react';

interface MessageBubbleProps {
    message: Message;
}

function CodeBlock({ language, value }: { language: string; value: string }) {
    return (
        <div className="my-3 rounded-xl overflow-hidden border border-[#2a2a2a]">
            {/* Code header bar */}
            <div className="flex items-center justify-between px-4 py-2 bg-[#1a1a2e] border-b border-[#2a2a2a]">
                <span className="text-[10px] font-mono text-[#555] uppercase tracking-widest">
                    {language || 'code'}
                </span>
            </div>
            <SyntaxHighlighter
                style={vscDarkPlus}
                language={language || 'text'}
                PreTag="div"
                customStyle={{
                    margin: 0,
                    padding: '1rem',
                    fontSize: '0.8125rem',
                    background: '#0d0d1a',
                    lineHeight: '1.6',
                }}
            >
                {value}
            </SyntaxHighlighter>
        </div>
    );
}

export function MessageBubble({ message }: MessageBubbleProps) {
    const isUser = message.role === 'user';

    return (
        <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} group`}>
            {/* Avatar */}
            <div
                className={`
          shrink-0 w-8 h-8 rounded-xl flex items-center justify-center mt-0.5
          ${isUser
                        ? 'bg-gradient-to-br from-[#1e3a5f] to-[#2a4a70] border border-[#3a5a80]'
                        : 'bg-gradient-to-br from-[#1a1a2e] to-[#252540] border border-[#2a2a4a]'
                    }
        `}
            >
                {isUser
                    ? <User size={14} className="text-[#7bb3ff]" />
                    : <Bot size={14} className="text-[#a78bfa]" />
                }
            </div>

            {/* Bubble */}
            <div
                className={`
          max-w-[75%] rounded-2xl px-4 py-3
          ${isUser
                        ? 'bg-gradient-to-br from-[#1e3a5f] to-[#162d4a] border border-[#2a4a70] text-[#ddeeff] rounded-tr-sm'
                        : 'bg-[#171717] border border-[#222] text-[#e0e0e0] rounded-tl-sm'
                    }
        `}
            >
                {isUser ? (
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                ) : (
                    <div className="prose-dark">
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                code({ inline, className, children, ...props }: any) {
                                    const match = /language-(\w+)/.exec(className || '');
                                    return !inline && match ? (
                                        <CodeBlock
                                            language={match[1]}
                                            value={String(children).replace(/\n$/, '')}
                                        />
                                    ) : (
                                        <code className={className} {...props}>
                                            {children}
                                        </code>
                                    );
                                },
                            }}
                        >
                            {message.content}
                        </ReactMarkdown>
                    </div>
                )}

                {/* Timestamp */}
                <p className={`text-[10px] mt-1.5 ${isUser ? 'text-[#4a7aaa] text-right' : 'text-[#444]'}`}>
                    {new Date(message.createdAt).toLocaleTimeString('ru-RU', {
                        hour: '2-digit',
                        minute: '2-digit',
                    })}
                </p>
            </div>
        </div>
    );
}
