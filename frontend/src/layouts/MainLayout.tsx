import Sidebar from '../components/sidebar/Sidebar';
import ChatArea from '../components/chat/ChatArea';

export default function MainLayout() {
    return (
        <div className="flex h-screen w-screen overflow-hidden">
            <Sidebar />
            <ChatArea />
        </div>
    );
}
