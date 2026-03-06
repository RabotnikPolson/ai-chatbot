import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import api from './api/axiosInstance';
import MainLayout from './layouts/MainLayout';
import AuthPage from './pages/AuthPage';
import useChatStore from './store/useChatStore';

// ─── Route Guard: redirect to /auth if not logged in ─────────────────────────

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const accessToken = useChatStore((s) => s.accessToken);
  // Простая тупая проверка: если нет токена — на авторизацию
  if (!accessToken) return <Navigate to="/auth" replace />;
  return <>{children}</>;
}

// ─── Auth Route: redirect to / if already logged in ──────────────────────────

function AuthRoute() {
  const accessToken = useChatStore((s) => s.accessToken);
  // Если токен есть — сразу пускаем в чат
  if (accessToken) return <Navigate to="/" replace />;
  return <AuthPage />;
}

// ─── App Routes ───────────────────────────────────────────────────────────────

function AppRoutes() {
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    let mounted = true;

    const initSession = async () => {
      try {
        const res = await api.post('/auth/refresh');
        if (mounted && res.data?.access_token) {
          useChatStore.getState().setAccessToken(res.data.access_token);
          useChatStore.getState().setUser({
            id: 'user-recovered',
            name: 'Recovered User',
            email: 'loaded-via-refresh@example.com'
          });
          useChatStore.getState().setWsStatus('connected');
        }
      } catch (err) {
        console.warn('Startup refresh failed (likely no session cookie).');
      } finally {
        if (mounted) setIsInitializing(false);
      }
    };

    // Only run if we don't have a token already (e.g. F5 reload)
    if (!useChatStore.getState().accessToken) {
      initSession();
    } else {
      setIsInitializing(false);
    }

    return () => { mounted = false; };
  }, []); // Run exactly once on mount

  if (isInitializing) {
    return (
      <div className="flex w-screen h-screen items-center justify-center bg-[#0d0d0d]">
        <div className="text-[#888] animate-pulse">Загрузка сессии...</div>
      </div>
    );
  }

  return (
    <Routes>
      {/* Public: auth page */}
      <Route path="/auth" element={<AuthRoute />} />

      {/* Protected: main chat */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      />
      <Route
        path="/chat/:chatId"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
