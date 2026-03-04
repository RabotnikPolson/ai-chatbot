import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
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

// ─── Logout Handler (needs router context) ────────────────────────────────────

export function useLogout() {
  const navigate = useNavigate();
  const setUser = useChatStore((s) => s.setUser);
  const setAccessToken = useChatStore((s) => s.setAccessToken);
  const setChats = useChatStore((s) => s.setChats);
  const setMessages = useChatStore((s) => s.setMessages);
  const setActiveChatId = useChatStore((s) => s.setActiveChatId);
  const setWsStatus = useChatStore((s) => s.setWsStatus);

  return async () => {
    try {
      // Бэкенд пока не готов, отключено чтобы избежать CORS-ошибок:
      // await api.post('/auth/logout');
    } catch (e) {
      console.error('Logout error:', e);
    } finally {
      setUser(null);
      setAccessToken(null);
      setChats([]);
      setMessages([]);
      setActiveChatId(null);
      setWsStatus('disconnected');
      navigate('/auth', { replace: true });
    }
  };
}

// ─── App Routes ───────────────────────────────────────────────────────────────

function AppRoutes() {
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
