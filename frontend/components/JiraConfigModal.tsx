"use client";
import { useState } from "react";
import { useSession } from "next-auth/react";
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
            await axios.post(
                `${process.env.NEXT_PUBLIC_API_URL}/users/${session.user.email}/jira-config`,
                form,
            );
            alert(" Đã lưu Jira config!");
            onSaved();
        } catch {
            alert(" Lưu thất bại, kiểm tra lại thông tin");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
            <div className="bg-gray-900 border border-gray-700 rounded-2xl p-8 w-full max-w-md space-y-5">
                <div>
                    <h2 className="text-xl font-bold text-white">
                        ⚙️ Kết nối Jira
                    </h2>
                    <p className="text-gray-400 text-sm mt-1">
                        Chỉ cần setup một lần — tự động dùng cho mọi export sau
                        này
                    </p>
                </div>

                <div className="space-y-3">
                    <div>
                        <label className="text-gray-400 text-sm">
                            Jira Site URL
                        </label>
                        <input
                            className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm text-white mt-1"
                            placeholder="https://yourcompany.atlassian.net"
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
                        <label className="text-gray-400 text-sm">
                            API Token
                        </label>
                        <input
                            type="password"
                            className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm text-white mt-1"
                            placeholder="ATATT3xFfGF0..."
                            value={form.jira_api_token}
                            onChange={(e) =>
                                setForm({
                                    ...form,
                                    jira_api_token: e.target.value,
                                })
                            }
                        />
                        {/* Sửa lỗi thẻ <a> tại đây */}
                        <a
                            href="https://id.atlassian.com/manage-profile/security/api-tokens"
                            target="_blank"
                            rel="noreferrer"
                            className="text-indigo-400 text-xs hover:underline mt-1 block"
                        >
                            Tạo API Token tại đây
                        </a>
                    </div>

                    <div>
                        <label className="text-gray-400 text-sm">
                            Project Key
                        </label>
                        <input
                            className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm text-white mt-1"
                            placeholder="SCRUM"
                            value={form.jira_project_key}
                            onChange={(e) =>
                                setForm({
                                    ...form,
                                    jira_project_key: e.target.value,
                                })
                            }
                        />
                    </div>
                </div>

                <button
                    onClick={handleSave}
                    disabled={
                        saving ||
                        !form.jira_site_url ||
                        !form.jira_api_token ||
                        !form.jira_project_key
                    }
                    className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition"
                >
                    {saving ? "Đang lưu..." : "Lưu & Kết nối Jira"}
                </button>
            </div>
        </div>
    );
}
