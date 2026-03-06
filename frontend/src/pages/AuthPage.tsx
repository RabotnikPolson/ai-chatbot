import { useState } from 'react';
import { Eye, EyeOff, Mail, Lock, User, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axiosInstance';
import useChatStore from '../store/useChatStore';
import type { User as UserType } from '../types';

// ─── Shared Input ─────────────────────────────────────────────────────────────

interface InputFieldProps {
    id: string;
    label: string;
    type: string;
    value: string;
    onChange: (v: string) => void;
    placeholder: string;
    icon: React.ReactNode;
    toggle?: React.ReactNode;
}

function InputField({ id, label, type, value, onChange, placeholder, icon, toggle }: InputFieldProps) {
    return (
        <div className="flex flex-col gap-1.5">
            <label htmlFor={id} className="text-xs font-medium text-[#888] uppercase tracking-wider">
                {label}
            </label>
            <div className="relative flex items-center">
                <span className="absolute left-3 text-[#555] pointer-events-none">{icon}</span>
                <input
                    id={id}
                    type={type}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={placeholder}
                    className="
                        w-full pl-9 pr-10 py-2.5 rounded-xl
                        bg-[#1a1a1a] border border-[#2a2a2a]
                        text-[#e0e0e0] placeholder-[#404040]
                        text-sm outline-none
                        focus:border-[#4f8ef7] focus:shadow-[0_0_0_3px_rgba(79,142,247,0.1)]
                        transition-all duration-200
                    "
                />
                {toggle && (
                    <span className="absolute right-3 text-[#555] cursor-pointer">{toggle}</span>
                )}
            </div>
        </div>
    );
}

// ─── Auth Page ────────────────────────────────────────────────────────────────

export default function AuthPage() {
    const navigate = useNavigate();
    const [tab, setTab] = useState<'login' | 'register'>('login');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [showPw, setShowPw] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const setUser = useChatStore((s) => s.setUser);
    const setAccessToken = useChatStore((s) => s.setAccessToken);
    const setWsStatus = useChatStore((s) => s.setWsStatus);

    const validate = (): string => {
        if (tab === 'register' && !name.trim()) return 'Введите ваше имя';
        if (!email.trim()) return 'Введите email';

        // Strict ASCII email validation
        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailRegex.test(email.trim())) return 'Некорректный формат email (используйте только латиницу)';

        if (!password) return 'Введите пароль';

        // Strict ASCII password validation
        const passwordRegex = /^[\x20-\x7E]+$/;
        if (!passwordRegex.test(password)) return 'Пароль должен содержать только латинские символы и цифры';

        if (password.length < 8) return 'Пароль должен содержать минимум 8 символов';

        return '';
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const validationError = validate();
        if (validationError) { setError(validationError); return; }
        setError('');

        setLoading(true);

        try {
            if (tab === 'register') {
                // Real Registration call
                await api.post('/auth/register', {
                    email: email.trim(),
                    password,
                    name: name.trim() || email.split('@')[0]
                });
            }

            // Real Login call using URLSearchParams for OAuth2PasswordRequestForm
            const params = new URLSearchParams();
            params.append('username', email.trim());
            params.append('password', password);

            const loginRes = await api.post('/auth/login', params, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });
            const { access_token } = loginRes.data;

            // Optional: fetch user info, or just mock structural state for now
            const user: UserType = {
                id: email.trim(),
                email: email.trim(),
                name: tab === 'register' ? name.trim() : email.split('@')[0],
            };

            setUser(user);
            setAccessToken(access_token);
            setWsStatus('connected');

            navigate('/', { replace: true });
        } catch (err: any) {
            console.error('Auth error:', err);
            setError(err.response?.data?.detail || 'Ошибка авторизации. Проверьте данные и попробуйте снова.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex h-[100dvh] w-screen items-center justify-center bg-[#0d0d0d] overflow-auto min-w-[320px] min-h-[550px]">
            {/* Ambient glow */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-[#4f8ef7] opacity-[0.04] rounded-full blur-3xl" />
                <div className="absolute bottom-1/4 left-1/2 -translate-x-1/2 w-[400px] h-[400px] bg-[#7c3aed] opacity-[0.04] rounded-full blur-3xl" />
            </div>

            <div className="relative z-10 w-full max-w-sm mx-4">
                {/* Brand */}
                <div className="flex flex-col items-center mb-8 gap-3">
                    <div className="relative">
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#4f8ef7] to-[#7c3aed] flex items-center justify-center shadow-2xl shadow-blue-900/40">
                            <Sparkles size={24} className="text-white" />
                        </div>
                        <div className="absolute -inset-1 rounded-2xl bg-gradient-to-br from-[#4f8ef7] to-[#7c3aed] opacity-25 blur-md -z-10" />
                    </div>
                    <div className="text-center">
                        <h1 className="text-xl font-bold text-[#e8e8e8] tracking-tight">VibeChat</h1>
                        <p className="text-xs text-[#555] mt-0.5">Local AI Assistant</p>
                    </div>
                </div>

                {/* Card */}
                <div className="bg-[#111111] border border-[#1e1e1e] rounded-2xl p-6 shadow-2xl shadow-black/60">
                    {/* Tabs */}
                    <div className="flex rounded-xl bg-[#0d0d0d] border border-[#1e1e1e] p-1 mb-6 gap-1">
                        {(['login', 'register'] as const).map((t) => (
                            <button
                                key={t}
                                onClick={() => { setTab(t); setError(''); }}
                                className={`
                                    flex-1 py-2 text-sm font-medium rounded-lg transition-all duration-200
                                    ${tab === t
                                        ? 'bg-gradient-to-r from-[#4f8ef7] to-[#7c3aed] text-white shadow-md'
                                        : 'text-[#666] hover:text-[#aaa]'
                                    }
                                `}
                            >
                                {t === 'login' ? 'Войти' : 'Регистрация'}
                            </button>
                        ))}
                    </div>

                    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                        {tab === 'register' && (
                            <InputField
                                id="name"
                                label="Имя"
                                type="text"
                                value={name}
                                onChange={setName}
                                placeholder="Ваше имя"
                                icon={<User size={15} />}
                            />
                        )}
                        <InputField
                            id="email"
                            label="Email"
                            type="email"
                            value={email}
                            onChange={setEmail}
                            placeholder="you@example.com"
                            icon={<Mail size={15} />}
                        />
                        <InputField
                            id="password"
                            label="Пароль"
                            type={showPw ? 'text' : 'password'}
                            value={password}
                            onChange={setPassword}
                            placeholder="••••••••"
                            icon={<Lock size={15} />}
                            toggle={
                                <span onClick={() => setShowPw((v) => !v)}>
                                    {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                                </span>
                            }
                        />

                        {error && (
                            <p className="text-xs text-[#e05555] bg-[#2a1111] border border-[#3a1515] rounded-lg px-3 py-2">
                                {error}
                            </p>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="
                                w-full py-2.5 mt-1 rounded-xl
                                bg-gradient-to-r from-[#4f8ef7] to-[#7c3aed]
                                text-white text-sm font-semibold
                                hover:opacity-90 active:scale-[0.99]
                                disabled:opacity-50 disabled:cursor-not-allowed
                                transition-all duration-200
                                shadow-md shadow-blue-900/30
                            "
                        >
                            {loading
                                ? 'Загрузка...'
                                : tab === 'login' ? 'Войти' : 'Создать аккаунт'
                            }
                        </button>
                    </form>
                </div>

                <p className="text-center text-[10px] text-[#333] mt-4">
                    Данные защищены httpOnly cookie · Refresh Token
                </p>
            </div>
        </div>
    );
}
