"use client";
import { useState, useEffect } from "react";

interface UserStory {
    title: string;
    role: string;
    action: string;
    benefit: string;
    acceptance_criteria: string[];
}

export default function UserStoryConfirm({
    story,
    onConfirm,
}: {
    story: UserStory;
    onConfirm: (edited: UserStory) => void;
}) {
    const [edited, setEdited] = useState<UserStory>({
        title: story?.title || "",
        role: story?.role || "",
        action: story?.action || "",
        benefit: story?.benefit || "",
        acceptance_criteria: story?.acceptance_criteria || [],
    });

    useEffect(() => {
        if (story) {
            setEdited({
                title: story.title || "",
                role: story.role || "",
                action: story.action || "",
                benefit: story.benefit || "",
                acceptance_criteria: story.acceptance_criteria || [],
            });
        }
    }, [story]);

    const update = (key: keyof UserStory, value: any) =>
        setEdited((prev) => ({ ...prev, [key]: value }));

    const addAC = () => {
        update("acceptance_criteria", [...edited.acceptance_criteria, ""]);
    };

    const removeAC = (index: number) => {
        const updated = edited.acceptance_criteria.filter(
            (_, i) => i !== index,
        );
        update("acceptance_criteria", updated);
    };

    const handleACChange = (index: number, value: string) => {
        const updated = [...edited.acceptance_criteria];
        updated[index] = value;
        update("acceptance_criteria", updated);
    };

    return (
        <div className="bg-gray-800 border-2 border-indigo-500 rounded-xl p-6 shadow-2xl space-y-6 animate-in fade-in zoom-in-95 duration-300">
            <div className="flex justify-between items-center border-b border-gray-700 pb-3">
                <h3 className="text-indigo-400 font-bold text-xl flex items-center gap-2">
                    Review & Finalize User Story
                </h3>
                <span className="text-xs text-gray-500 italic">
                    BA Mode: Editable
                </span>
            </div>

            <div className="space-y-4">
                <Field
                    label="Story Title"
                    value={edited.title}
                    onChange={(v) => update("title", v)}
                    placeholder="Ví dụ: Thanh toán qua ví MoMo"
                />

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Field
                        label="As a (Role)"
                        value={edited.role}
                        onChange={(v) => update("role", v)}
                    />
                    <Field
                        label="I want to (Action)"
                        value={edited.action}
                        onChange={(v) => update("action", v)}
                    />
                    <Field
                        label="So that (Benefit)"
                        value={edited.benefit}
                        onChange={(v) => update("benefit", v)}
                    />
                </div>

                <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700">
                    <div className="flex justify-between items-center mb-2">
                        <label className="text-indigo-300 text-sm font-semibold uppercase tracking-wider">
                            Acceptance Criteria
                        </label>
                        <button
                            onClick={addAC}
                            type="button"
                            className="text-xs bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-400 px-2 py-1 rounded border border-indigo-600/50 transition-all"
                        >
                            + Add Criteria
                        </button>
                    </div>

                    <div className="space-y-2">
                        {edited.acceptance_criteria.map((ac, i) => (
                            <div key={i} className="flex gap-2 items-center">
                                <span className="text-gray-600 text-xs w-4">
                                    {i + 1}.
                                </span>
                                <input
                                    className="flex-1 bg-gray-800 border border-gray-700 focus:border-indigo-500 rounded px-3 py-2 text-sm text-gray-200 outline-none transition-colors"
                                    value={ac || ""}
                                    placeholder="Điều kiện để tính năng được nghiệm thu..."
                                    onChange={(e) =>
                                        handleACChange(i, e.target.value)
                                    }
                                />
                                <button
                                    type="button"
                                    onClick={() => removeAC(i)}
                                    className="text-gray-500 hover:text-red-400 px-1 transition-colors"
                                    title="Xóa tiêu chí này"
                                >
                                    ✕
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <div className="flex justify-end pt-4">
                <button
                    onClick={() => onConfirm(edited)}
                    className="group relative inline-flex items-center justify-center px-8 py-3 font-bold text-white transition-all duration-200 bg-indigo-600 font-pj rounded-xl hover:bg-indigo-700 shadow-lg shadow-indigo-500/30 active:scale-95"
                >
                    Xác nhận & Phân rã Task Kỹ thuật
                </button>
            </div>
        </div>
    );
}

function Field({
    label,
    value,
    onChange,
    placeholder = "",
}: {
    label: string;
    value: string;
    onChange: (v: string) => void;
    placeholder?: string;
}) {
    return (
        <div className="flex flex-col gap-1.5">
            <label className="text-gray-400 text-xs font-medium uppercase tracking-tighter">
                {label}
            </label>
            <input
                className="w-full bg-gray-900 border border-gray-700 focus:border-indigo-500 rounded-lg px-4 py-2.5 text-sm text-gray-100 outline-none transition-all placeholder:text-gray-600 shadow-inner"
                value={value || ""}
                placeholder={placeholder}
                onChange={(e) => onChange(e.target.value)}
            />
        </div>
    );
}
