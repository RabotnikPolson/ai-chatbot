import { useState } from 'react';
import Sidebar from '../components/sidebar/Sidebar';
import ChatArea from '../components/chat/ChatArea';

export default function MainLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(true);

    return (
        // min-w prevents horizontal collapse, min-h prevents vertical collapse
        <div className="flex w-screen h-[100dvh] overflow-y-auto min-w-[320px] min-h-[550px]">
            <Sidebar isOpen={sidebarOpen} />
            <ChatArea
                onToggleSidebar={() => setSidebarOpen((v) => !v)}
                sidebarOpen={sidebarOpen}
            />
        </div>
    );
}
