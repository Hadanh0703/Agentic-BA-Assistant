"use client";
import { useState, useRef, useEffect } from "react";
import AgentStatusBar from "./AgentStatusBar";
import UserStoryConfirm from "./UserStoryConfirm";
import RiskReport from "./RiskReport";
import ChatSkeleton from "./ChatSkeleton";
import { useWebSocket } from "@/hooks/useWebSocket";

export default function ChatWindow({
    projectId,
    messages,
    onSendMessage,
    isLoading,
    isLoadingHistory,
    pendingStory,
    onConfirm,
    tasks,
    onViewWorkspace,
}: any) {
    const { agentStatus } = useWebSocket(projectId);
    const [input, setInput] = useState("");
    const bottomRef = useRef<HTMLDivElement>(null);

    const latestRiskReport =
        tasks?.length > 0 ? tasks[tasks.length - 1]?.risk_report : null;

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, agentStatus]);

    const handleSend = async (text?: string) => {
        const msg = text ?? input;
        if (!msg.trim() || isLoading) return;
        setInput("");
        await onSendMessage(msg);
    };

    if (isLoadingHistory) return <ChatSkeleton />;

    return (
        <div className="flex flex-col h-screen bg-gray-950 text-white">
            {/* Banner Workspace */}
            {tasks?.length > 0 && (
                <div className="bg-indigo-950/40 border-b border-indigo-500/30 px-6 py-2 flex justify-between items-center animate-in fade-in duration-500">
                    <span className="text-xs text-indigo-300 font-large italic">
                        Xem danh sách Task do AI phân tách
                    </span>
                    <button
                        onClick={onViewWorkspace}
                        className="text-xs bg-indigo-600 hover:bg-indigo-500 px-5 py-2 rounded-lg transition-colors font-semibold"
                    >
                        Mở Workspace →
                    </button>
                </div>
            )}

            {latestRiskReport && (
                <div className="px-6 pt-3 pb-1 border-b border-gray-800/50">
                    <RiskReport report={latestRiskReport} />
                </div>
            )}

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.map((m: any, i: number) => (
                    <div
                        key={i}
                        className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                        <div
                            className={`max-w-2xl px-4 py-3 rounded-xl text-sm ${m.role === "user" ? "bg-indigo-600" : "bg-gray-800"}`}
                        >
                            {m.agent_name && (
                                <p className="text-xs text-indigo-400 mb-1 font-semibold">
                                    {m.agent_name}
                                </p>
                            )}
                            <div className="whitespace-pre-wrap">
                                {m.content}
                            </div>
                            {m.content.includes("Đã phân rã") && (
                                <button
                                    onClick={onViewWorkspace}
                                    className="mt-3 w-full py-2 bg-indigo-500 hover:bg-indigo-400 text-white rounded-lg font-bold transition-all shadow-lg shadow-indigo-500/20"
                                >
                                    Xem chi tiết Task Workspace
                                </button>
                            )}
                        </div>
                    </div>
                ))}

                {isLoading && agentStatus && (
                    <AgentStatusBar
                        step={agentStatus.step}
                        message={agentStatus.message}
                    />
                )}
                {pendingStory && !isLoading && (
                    <UserStoryConfirm
                        story={pendingStory}
                        onConfirm={onConfirm}
                    />
                )}
                <div ref={bottomRef} />
            </div>

            <div className="border-t border-gray-800 p-4 flex gap-3 bg-gray-950">
                <input
                    className="flex-1 bg-gray-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                    placeholder={
                        pendingStory
                            ? "Vui lòng xác nhận User Story..."
                            : "Nhập yêu cầu..."
                    }
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                    disabled={isLoading || !!pendingStory}
                />
                <button
                    onClick={() => handleSend()}
                    disabled={isLoading || !!pendingStory}
                    className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 px-6 py-3 rounded-xl font-bold text-sm transition-all"
                >
                    Gửi
                </button>
            </div>
        </div>
    );
}
