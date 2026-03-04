import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import useChatStore from './store/useChatStore';

function AppRoutes() {
  const loadMockData = useChatStore((s) => s.loadMockData);

  useEffect(() => {
    // Load mock data on mount (replace with real auth/API calls later)
    loadMockData();
  }, [loadMockData]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />} />
        <Route path="/chat/:chatId" element={<MainLayout />} />
        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default function App() {
  return <AppRoutes />;
}
