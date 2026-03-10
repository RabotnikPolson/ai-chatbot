import React from 'react';
import { useAuthStore } from '../store/authStore';

interface LayoutProps {
    children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
    const logout = useAuthStore((state) => state.logout);

    return (
        <div className="h-screen flex bg-gray-50">
            {/* Сайдбар */}
            <div className="w-64 bg-gray-900 text-white flex flex-col">
                {/* Верх (статика) */}
                <div className="p-4 border-b border-gray-800">
                    <h1 className="text-xl font-bold mb-4">AI Bot</h1>
                    <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded transition">
                        Новый чат
                    </button>
                </div>

                {/* Середина (динамика, скролл) */}
                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                    <div className="p-2 hover:bg-gray-800 rounded cursor-pointer transition truncate">
                        Чат про React
                    </div>
                    <div className="p-2 hover:bg-gray-800 rounded cursor-pointer transition truncate">
                        Что такое FastAPI?
                    </div>
                    <div className="p-2 hover:bg-gray-800 rounded cursor-pointer transition truncate">
                        Помоги написать код
                    </div>
                </div>

                {/* Низ (статика) */}
                <div className="p-4 border-t border-gray-800">
                    <button
                        onClick={logout}
                        className="w-full text-left text-gray-300 hover:text-white hover:bg-gray-800 p-2 rounded transition"
                    >
                        Выйти
                    </button>
                </div>
            </div>

            {/* Основная зона */}
            <div className="flex-1 flex flex-col">
                {children}
            </div>
        </div>
    );
};

export default Layout;
