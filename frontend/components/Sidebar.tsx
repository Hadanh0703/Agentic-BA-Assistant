"use client";
import { useState, useEffect } from "react";
import { useProjects } from "@/hooks/useProjects";
import { projectsApi } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useSession, signOut } from "next-auth/react";

export default function Sidebar({ activeId }: { activeId?: number }) {
    const { projects, createProject, deleteProject } = useProjects();
    const [newName, setNewName] = useState("");
    const [uploading, setUploading] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
    const router = useRouter();
    const { data: session } = useSession();

    const handleCreate = async () => {
        if (!newName.trim()) return;
        await createProject(newName.trim());
        setNewName("");
    };

    const handleUpload = async (file: File) => {
        if (!activeId || isNaN(activeId)) {
            alert("Vui lòng chọn một dự án trước khi nạp tài liệu!");
            return;
        }
        setUploading(true);
        const formData = new FormData();
        formData.append("file", file);
        try {
            await projectsApi.uploadFile(activeId, formData);
            setUploadedFiles((prev) => [...prev, file.name]);
            alert(`Đã nạp "${file.name}" thành công!`);
        } catch (error: any) {
            const errorMsg = error.response?.data?.detail || "Lỗi server.";
            alert(`Upload thất bại: ${errorMsg}`);
        } finally {
            setUploading(false);
        }
    };

    const handleRemoveFile = async (fileName: string) => {
        if (!activeId) return;
        if (!confirm(`Bạn muốn gỡ bỏ tri thức từ file "${fileName}"?`)) return;
        try {
            await projectsApi.deleteFile(activeId, fileName);
            setUploadedFiles((prev) =>
                prev.filter((name) => name !== fileName),
            );
            alert("Đã gỡ bỏ file thành công.");
        } catch (error) {
            alert("Không thể xóa file. Vui lòng kiểm tra lại Backend.");
        }
    };

    useEffect(() => {
        const loadFiles = async () => {
            if (activeId) {
                try {
                    const res = await projectsApi.getFiles(activeId);
                    setUploadedFiles(res.data.map((f: any) => f.file_name));
                } catch (error) {
                    console.error("Không thể load danh sách file");
                }
            } else {
                setUploadedFiles([]);
            }
        };
        loadFiles();
    }, [activeId]);

    return (
        <aside className="w-64 bg-gray-950 text-white flex flex-col h-screen p-4 gap-4 border-r border-gray-800 shadow-2xl">
            <h1 className="text-xl font-bold text-indigo-400 tracking-tight">
                AI-BA Assistant
            </h1>

            <div className="flex gap-2 items-center">
                <input
                    className="min-w-0 flex-1 bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-all placeholder:text-gray-600"
                    placeholder="Tên dự án mới..."
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                />
                <button
                    onClick={handleCreate}
                    className="flex-shrink-0 w-10 h-10 bg-indigo-600 hover:bg-indigo-500 flex items-center justify-center rounded-lg text-xl transition-all shadow-lg shadow-indigo-600/20 active:scale-95"
                >
                    +
                </button>
            </div>

            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mt-2">
                Danh sách dự án
            </div>

            <div className="flex-1 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
                {projects.map((p) => (
                    <div
                        key={p.id}
                        onClick={() => router.push(`/projects/${p.id}`)}
                        className={`group flex justify-between items-center px-3 py-2.5 rounded-xl cursor-pointer text-sm transition-all ${
                            activeId === p.id
                                ? "bg-indigo-600 shadow-lg shadow-indigo-600/20 text-white"
                                : "text-gray-400 hover:bg-gray-900 hover:text-gray-200"
                        }`}
                    >
                        <span className="truncate font-medium">{p.name}</span>
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                if (
                                    confirm(
                                        "Xóa dự án này sẽ mất toàn bộ tin nhắn và file liên quan?",
                                    )
                                )
                                    deleteProject(p.id);
                            }}
                            className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 transition-all px-1"
                        >
                            ✕
                        </button>
                    </div>
                ))}
            </div>

            <div className="mt-auto border-t border-gray-800 pt-4 space-y-3">
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Cơ sở tri thức (PDF)
                </div>

                <div className="space-y-2 max-h-32 overflow-y-auto custom-scrollbar">
                    {uploadedFiles.map((fileName, idx) => (
                        <div
                            key={idx}
                            className="flex items-center justify-between bg-gray-900 border border-gray-800 px-3 py-2 rounded-lg group"
                        >
                            <span className="text-xs text-gray-300 truncate pr-2 flex items-center gap-2">
                                <span className="text-indigo-400">📄</span>
                                {fileName}
                            </span>
                            <button
                                onClick={() => handleRemoveFile(fileName)}
                                className="text-gray-600 hover:text-red-400 transition-colors text-xs"
                            >
                                ✕
                            </button>
                        </div>
                    ))}
                </div>

                <label
                    className={`w-full flex items-center justify-center gap-2 py-3 rounded-xl border border-dashed border-gray-700 transition-all ${
                        !activeId
                            ? "opacity-50 cursor-not-allowed"
                            : "hover:border-indigo-500 hover:bg-indigo-500/5 cursor-pointer"
                    }`}
                >
                    {uploading ? (
                        <div className="flex items-center gap-2 text-yellow-500 text-sm font-medium">
                            <div className="w-4 h-4 border-2 border-yellow-500 border-t-transparent animate-spin rounded-full"></div>
                            Đang nạp...
                        </div>
                    ) : (
                        <>
                            <span className="text-xl text-indigo-400">+</span>
                            <span className="text-sm font-medium text-gray-300">
                                Nạp tài liệu PDF
                            </span>
                            <input
                                type="file"
                                accept=".pdf"
                                className="hidden"
                                disabled={!activeId || uploading}
                                onChange={(e) => {
                                    const f = e.target.files?.[0];
                                    if (f) handleUpload(f);
                                    e.target.value = "";
                                }}
                            />
                        </>
                    )}
                </label>

                <div className="border-t border-gray-800 pt-3 flex items-center justify-between gap-2 overflow-hidden">
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                        {session?.user?.image ? (
                            <img
                                src={session.user.image}
                                alt="avatar"
                                className="w-7 h-7 rounded-full flex-shrink-0 ring-1 ring-gray-700"
                            />
                        ) : (
                            <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-xs font-bold flex-shrink-0">
                                {session?.user?.name?.[0]?.toUpperCase() ?? "U"}
                            </div>
                        )}
                        <div className="min-w-0 flex-1 overflow-hidden">
                            <p className="text-xs font-medium text-gray-300 truncate">
                                {session?.user?.name ?? "User"}
                            </p>
                            <p className="text-xs text-gray-600 truncate">
                                {session?.user?.email}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={() => signOut({ callbackUrl: "/login" })}
                        className="flex-shrink-0 text-gray-500 hover:text-red-400 transition-colors p-1.5 rounded-lg hover:bg-red-400/10"
                        title="Đăng xuất"
                    >
                        ⏻
                    </button>
                </div>
            </div>
        </aside>
    );
}
