"use client";
import { useState } from "react";
import { useSession } from "next-auth/react";
// Import instance 'api' đã cấu hình baseURL từ lib/api
import { projectsApi } from "@/lib/api";
import axios from "axios";

export default function JiraConfigModal({ onSaved }: { onSaved: () => void }) {
    const { data: session } = useSession();
    const [form, setForm] = useState({
        jira_site_url: "",
        jira_api_token: "",
        jira_project_key: "",
    });
    const [saving, setSaving] = useState(false);

    const handleSave = async () => {
        if (!session?.user?.email) return;
        setSaving(true);

        try {
            // Sử dụng biến môi trường trực tiếp để đảm bảo độ chính xác cho Client Component
            const baseUrl = process.env.NEXT_PUBLIC_API_URL;

            await axios.post(
                `${baseUrl}/users/${session.user.email}/jira-config`,
                form,
            );

            alert(" Đã lưu cấu hình Jira thành công!");
            onSaved();
        } catch (error: any) {
            console.error("Jira Config Error:", error);
            alert(
                " Lưu thất bại. Vui lòng kiểm tra kết nối mạng hoặc server Railway.",
            );
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-900 border border-gray-700 rounded-2xl p-8 w-full max-w-md space-y-5 shadow-2xl">
                <div>
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        <span>⚙️</span> Kết nối Jira Cloud
                    </h2>
                    <p className="text-gray-400 text-sm mt-1">
                        Thiết lập một lần để xuất yêu cầu từ SmartGym Pro thẳng
                        lên Jira[cite: 1, 2].
                    </p>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="text-gray-400 text-xs uppercase font-semibold">
                            Jira Site URL
                        </label>
                        <input
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white mt-1 focus:outline-none focus:border-indigo-500"
                            placeholder="https://your-company.atlassian.net"
                            value={form.jira_site_url}
                            onChange={(e) =>
                                setForm({
                                    ...form,
                                    jira_site_url: e.target.value,
                                })
                            }
                        />
                    </div>

                    <div>
                        <label className="text-gray-400 text-xs uppercase font-semibold">
                            API Token
                        </label>
                        <input
                            type="password"
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white mt-1 focus:outline-none focus:border-indigo-500"
                            placeholder="ATATT3xFfGF0..."
                            value={form.jira_api_token}
                            onChange={(e) =>
                                setForm({
                                    ...form,
                                    jira_api_token: e.target.value,
                                })
                            }
                        />
                        <a
                            href="https://id.atlassian.com/manage-profile/security/api-tokens"
                            target="_blank"
                            rel="noreferrer"
                            className="text-indigo-400 text-xs hover:underline mt-2 block"
                        >
                            Lấy token tại Atlassian Security
                        </a>
                    </div>

                    <div>
                        <label className="text-gray-400 text-xs uppercase font-semibold">
                            Project Key
                        </label>
                        <input
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white mt-1 focus:outline-none focus:border-indigo-500"
                            placeholder="Ví dụ: SGPRO"
                            value={form.jira_project_key}
                            onChange={(e) =>
                                setForm({
                                    ...form,
                                    jira_project_key:
                                        e.target.value.toUpperCase(),
                                })
                            }
                        />
                    </div>
                </div>

                <div className="pt-2">
                    <button
                        onClick={handleSave}
                        disabled={
                            saving ||
                            !form.jira_site_url ||
                            !form.jira_api_token ||
                            !form.jira_project_key
                        }
                        className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-indigo-500/20"
                    >
                        {saving
                            ? "⏳ Đang kết nối..."
                            : "Lưu cấu hình & Bắt đầu"}
                    </button>
                </div>
            </div>
        </div>
    );
}
