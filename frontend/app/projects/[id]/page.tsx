"use client";

import { useState, useEffect, use } from "react";
import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import TaskWorkspace from "@/components/TaskWorkspace";
import { useChat } from "@/hooks/useChat";

export default function ProjectPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = use(params);
    const projectId = parseInt(id);

    const {
        messages,
        sendMessage,
        isLoading,
        isLoadingHistory,
        pendingStory,
        confirmStory,
        deleteStory,
        tasks,
        riskReport,
        justFinishedConfirm,
        setJustFinishedConfirm,
    } = useChat(projectId);

    const [activeView, setActiveView] = useState<"chat" | "workspace">("chat");

    useEffect(() => {
        if (justFinishedConfirm) {
            setActiveView("workspace");
            setJustFinishedConfirm(false);
        }
    }, [justFinishedConfirm, setJustFinishedConfirm]);

    const handleBackToChat = () => {
        setJustFinishedConfirm(false);
        setActiveView("chat");
    };

    return (
        <div className="flex h-screen bg-[#0a0a0a]">
            <Sidebar activeId={projectId} />
            <main className="flex-1 overflow-hidden relative">
                {activeView === "chat" ? (
                    <ChatWindow
                        projectId={projectId}
                        messages={messages}
                        onSendMessage={sendMessage}
                        isLoading={isLoading}
                        isLoadingHistory={isLoadingHistory}
                        pendingStory={pendingStory}
                        onConfirm={confirmStory}
                        tasks={tasks}
                        riskReport={riskReport}
                        onViewWorkspace={() => setActiveView("workspace")}
                    />
                ) : (
                    <TaskWorkspace
                        tasks={tasks}
                        onBackToChat={handleBackToChat}
                        onDeleteStory={deleteStory}
                    />
                )}
            </main>
        </div>
    );
}
