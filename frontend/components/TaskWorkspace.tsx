"use client";
import { useState } from "react";
import TaskTable from "./TaskTable";
import RiskReport from "./RiskReport";

interface TaskGroup {
    id?: number;
    story_details: {
        title: string;
        role: string;
        action: string;
        benefit: string;
        acceptance_criteria: string[];
    };
    items: any[];
    risk_report?: any;
    created_at: string;
}

interface TaskWorkspaceProps {
    tasks: TaskGroup[];
    onBackToChat: () => void;
    onDeleteStory: (artifactId: number) => void;
}

export default function TaskWorkspace({
    tasks,
    onBackToChat,
    onDeleteStory,
}: TaskWorkspaceProps) {
    const [expandedAC, setExpandedAC] = useState<Record<string, boolean>>({});
    const [isExporting, setIsExporting] = useState(false);

    const toggleAC = (uniqueKey: string) => {
        setExpandedAC((prev) => ({ ...prev, [uniqueKey]: !prev[uniqueKey] }));
    };

    const sortedTasks = tasks ? [...tasks].reverse() : [];

    const allItems = tasks?.flatMap((group) => group.items || []) || [];
    const totalSP = allItems.reduce(
        (sum, task) => sum + (Number(task.story_point) || 0),
        0,
    );

    // --- LOGIC EXPORT JIRA ---
    const handleExportJira = async (scope: "latest" | "all") => {
        if (!tasks || tasks.length === 0)
            return alert("Không có dữ liệu để export!");

        const confirmMsg =
            scope === "latest"
                ? "Bạn muốn đẩy Story mới nhất lên Jira?"
                : `Bạn muốn đẩy TẤT CẢ ${tasks.length} Stories lên Jira?`;

        if (!confirm(confirmMsg)) return;

        setIsExporting(true);
        try {
            const dataToExport =
                scope === "latest" ? [sortedTasks[0]] : sortedTasks;

            const response = await fetch(
                "http://localhost:8000/api/jira/export",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        stories: dataToExport.map((group) => ({
                            story_details: group.story_details,
                            tasks: group.items,
                        })),
                    }),
                },
            );

            if (response.ok) {
                alert(` Đồng bộ thành công lên Jira Cloud!`);
            } else {
                const result = await response.json();
                // ✅ Log chi tiết hơn để debug
                console.error("Jira error detail:", result);
                alert(` Lỗi: ${result.detail || JSON.stringify(result)}`);
            }
        } catch (error) {
            alert(" Lỗi kết nối đến Backend!");
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <div className="h-full flex flex-col bg-[#050505] text-white">
            <header className="border-b border-gray-800 p-6 flex justify-between items-center bg-[#0a0a0a] sticky top-0 z-10">
                <div>
                    <button
                        onClick={onBackToChat}
                        className="text-indigo-400 hover:text-indigo-300 text-sm flex items-center gap-2 mb-2 transition-colors font-medium"
                    >
                        ← Quay lại Chat
                    </button>
                    <h1 className="text-3xl font-bold tracking-tight text-white">
                        Project Workspace
                    </h1>
                    <div className="flex gap-4 mt-2">
                        <span className="text-[11px] font-medium text-gray-400 bg-gray-900 px-2.5 py-1 rounded border border-gray-800 shadow-sm">
                            📦 {tasks?.length || 0} Stories
                        </span>
                        <span className="text-[11px] font-medium text-gray-400 bg-gray-900 px-2.5 py-1 rounded border border-gray-800 shadow-sm">
                            ✅ {allItems.length} Total Tasks
                        </span>
                        <span className="text-[11px] font-medium text-gray-400 bg-gray-900 px-2.5 py-1 rounded border border-gray-800 shadow-sm">
                            🔥 {totalSP} Total SP
                        </span>
                    </div>
                </div>

                <div className="flex gap-3">
                    {/* Export Story mới nhất */}
                    <button
                        onClick={() => handleExportJira("latest")}
                        disabled={isExporting}
                        className="bg-gray-800 hover:bg-gray-700 text-white px-4 py-2.5 rounded-xl text-sm font-bold transition-all disabled:opacity-50 border border-gray-700"
                    >
                        {isExporting ? "Processing..." : "Export Latest"}
                    </button>

                    {/* Sync toàn bộ */}
                    <button
                        onClick={() => handleExportJira("all")}
                        disabled={isExporting}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-xl text-sm font-bold transition-all shadow-lg shadow-indigo-600/20 active:scale-95 disabled:opacity-50"
                    >
                        {isExporting ? "Syncing..." : "Sync All to Jira"}
                    </button>
                </div>
            </header>

            <div className="flex-1 overflow-y-auto p-8 space-y-20 custom-scrollbar">
                {sortedTasks.length > 0 ? (
                    sortedTasks.map((group, index) => {
                        const displayOrder = sortedTasks.length - index;
                        const uniqueIdentifier = group.id
                            ? `group-${group.id}`
                            : `group-order-${displayOrder}`;

                        const details = group.story_details;

                        return (
                            <section
                                key={uniqueIdentifier}
                                className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700"
                            >
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between border-b border-gray-800 pb-3">
                                        <div className="flex items-center gap-4">
                                            <span className="w-9 h-9 bg-indigo-500/10 border border-indigo-500/30 rounded-xl flex items-center justify-center text-indigo-400 text-sm font-black">
                                                {displayOrder}
                                            </span>
                                            <h2 className="text-xl font-bold text-white">
                                                {details?.title ||
                                                    "Untitled User Story"}
                                            </h2>
                                            <button
                                                onClick={() => {
                                                    if (
                                                        confirm(
                                                            "Bạn có chắc chắn muốn xóa vĩnh viễn bảng Task này không?",
                                                        )
                                                    ) {
                                                        onDeleteStory(
                                                            group.id!,
                                                        );
                                                    }
                                                }}
                                                className="p-1.5 text-gray-600 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all"
                                                title="Xóa vĩnh viễn"
                                            >
                                                🗑️
                                            </button>
                                        </div>
                                        <span className="text-[10px] text-gray-500 font-mono tracking-tighter bg-gray-900/50 px-2 py-1 rounded border border-gray-800/50">
                                            {group.created_at
                                                ? new Date(
                                                      group.created_at,
                                                  ).toLocaleString("vi-VN")
                                                : "Vừa khởi tạo"}
                                        </span>
                                    </div>

                                    <div className="bg-gray-900/20 border-l-4 border-indigo-500 p-5 rounded-r-2xl shadow-inner border border-y-gray-800 border-r-gray-800">
                                        <p className="text-base leading-relaxed text-gray-300">
                                            <span className="text-indigo-400 font-black italic">
                                                As a
                                            </span>{" "}
                                            <span className="text-white font-medium">
                                                {details?.role || "..."}
                                            </span>
                                            ,{" "}
                                            <span className="text-indigo-400 font-black italic">
                                                I want to
                                            </span>{" "}
                                            <span className="text-white font-medium">
                                                {details?.action || "..."}
                                            </span>
                                            ,{" "}
                                            <span className="text-indigo-400 font-black italic">
                                                so that
                                            </span>{" "}
                                            <span className="text-white font-medium">
                                                {details?.benefit || "..."}
                                            </span>
                                            .
                                        </p>

                                        <button
                                            onClick={() =>
                                                toggleAC(uniqueIdentifier)
                                            }
                                            className="mt-4 flex items-center gap-1.5 text-sm font-medium text-slate-400 hover:text-indigo-400 transition-colors duration-200 group cursor-pointer"
                                        >
                                            <span
                                                className={`transition-transform duration-300 ${expandedAC[uniqueIdentifier] ? "rotate-90" : ""}`}
                                            >
                                                ▶
                                            </span>
                                            {expandedAC[uniqueIdentifier]
                                                ? "Hide Acceptance Criteria"
                                                : "View Acceptance Criteria"}
                                        </button>

                                        {expandedAC[uniqueIdentifier] && (
                                            <div className="mt-4 space-y-2 pl-4 border-t border-gray-800/50 pt-4 animate-in slide-in-from-top-2 duration-300">
                                                {details?.acceptance_criteria?.map(
                                                    (ac, i) => (
                                                        <div
                                                            key={`${uniqueIdentifier}-ac-${i}`}
                                                            className="text-[13px] text-gray-400 flex gap-3 items-start"
                                                        >
                                                            <span className="text-indigo-500 font-bold mt-1 text-[10px]">
                                                                ●
                                                            </span>
                                                            <span className="flex-1">
                                                                {ac}
                                                            </span>
                                                        </div>
                                                    ),
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="bg-[#0a0a0a] border border-gray-800/50 rounded-2xl overflow-hidden shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
                                    <TaskTable
                                        initialTasks={group.items || []}
                                        artifactId={group.id || 0}
                                    />
                                </div>

                                {group.risk_report && (
                                    <div className="mx-2 p-5 border border-red-500/20 bg-red-500/[0.02] rounded-2xl">
                                        <h3 className="flex items-center gap-2 mb-3 text-[14px] font-bold text-rose-600 uppercase tracking-wider">
                                            <span className="animate-pulse text-lg">
                                                ⚠️
                                            </span>
                                            Risk Assessment Report
                                        </h3>
                                        <RiskReport
                                            report={group.risk_report}
                                        />
                                    </div>
                                )}
                            </section>
                        );
                    })
                ) : (
                    <div className="h-96 flex flex-col items-center justify-center border-2 border-dashed border-gray-800 rounded-[3rem] text-gray-600 bg-gray-900/10">
                        <div className="text-4xl mb-4 opacity-20">🗄️</div>
                        <p className="text-lg font-bold tracking-tight opacity-40 uppercase">
                            No User Stories Found
                        </p>
                    </div>
                )}
            </div>

            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 6px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: #050505;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #1f1f1f;
                    border-radius: 10px;
                }
            `}</style>
        </div>
    );
}
