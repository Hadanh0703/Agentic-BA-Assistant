"use client";
import { useState } from "react";
import { projectsApi } from "@/lib/api";

const PRIORITY_COLOR: Record<string, string> = {
    High: "text-red-400",
    Medium: "text-yellow-400",
    Low: "text-green-400",
};

const TYPE_COLOR: Record<string, string> = {
    FE: "bg-blue-800 text-blue-200",
    BE: "bg-green-800 text-green-200",
    DB: "bg-purple-800 text-purple-200",
};

interface Task {
    type: string;
    title: string;
    description: string;
    story_point: number | string;
    priority: string;
    assignee_suggestion: string;
}

export default function TaskTable({
    initialTasks,
    artifactId,
}: {
    initialTasks: Task[];
    artifactId: number;
}) {
    const [tasks, setTasks] = useState<Task[]>(initialTasks);
    const [isSaving, setIsSaving] = useState(false);

    const updateTaskField = (index: number, field: keyof Task, value: any) => {
        const newTasks = [...tasks];
        newTasks[index] = { ...newTasks[index], [field]: value };
        setTasks(newTasks);
    };

    const addTask = () => {
        const newTask: Task = {
            type: "BE",
            title: "New Task Name",
            description: "Task description...",
            story_point: 1,
            priority: "Medium",
            assignee_suggestion: "Developer",
        };
        setTasks([...tasks, newTask]);
    };

    const removeTask = (index: number) => {
        setTasks(tasks.filter((_, i) => i !== index));
    };

    const saveChanges = async () => {
        setIsSaving(true);
        try {
            await projectsApi.updateArtifact(artifactId, { tasks: tasks });
            alert("Đã lưu thay đổi vào hệ thống!");
        } catch (error) {
            alert("Lỗi khi lưu: " + error);
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center">
                <button
                    onClick={addTask}
                    className="text-xs bg-gray-800 hover:bg-gray-700 text-indigo-400 border border-indigo-500/30 px-3 py-1.5 rounded-lg transition-all"
                >
                    + Thêm Task thủ công
                </button>
                <button
                    onClick={saveChanges}
                    disabled={isSaving}
                    className={`text-xs px-4 py-1.5 rounded-lg font-bold transition-all ${
                        isSaving
                            ? "bg-gray-700 text-gray-500"
                            : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20"
                    }`}
                >
                    {isSaving ? "Đang lưu..." : "Lưu thay đổi"}
                </button>
            </div>

            <div className="overflow-x-auto rounded-xl border border-gray-700 bg-gray-900/50">
                <table className="w-full text-sm text-left">
                    <thead className="bg-gray-800/80 text-gray-400 uppercase text-xs">
                        <tr>
                            <th className="px-4 py-3 w-24">Type</th>
                            <th className="px-4 py-3">Title</th>
                            <th className="px-4 py-3">Description</th>
                            <th className="px-4 py-3 w-16">SP</th>
                            <th className="px-4 py-3 w-28">Priority</th>
                            <th className="px-4 py-3">Assignee</th>
                            <th className="px-4 py-3 w-10 text-center"></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-800">
                        {tasks.map((t, i) => (
                            <tr
                                key={i}
                                className="group hover:bg-gray-800/30 transition-colors"
                            >
                                <td className="px-4 py-2">
                                    <select
                                        value={t.type}
                                        onChange={(e) =>
                                            updateTaskField(
                                                i,
                                                "type",
                                                e.target.value,
                                            )
                                        }
                                        className={`bg-transparent outline-none rounded px-1 font-bold text-xs ${TYPE_COLOR[t.type] ?? "text-gray-400"}`}
                                    >
                                        <option
                                            value="FE"
                                            className="bg-gray-900"
                                        >
                                            FE
                                        </option>
                                        <option
                                            value="BE"
                                            className="bg-gray-900"
                                        >
                                            BE
                                        </option>
                                        <option
                                            value="DB"
                                            className="bg-gray-900"
                                        >
                                            DB
                                        </option>
                                    </select>
                                </td>
                                <td className="px-4 py-2">
                                    <input
                                        className="bg-transparent border-none outline-none focus:ring-1 focus:ring-indigo-500 rounded px-1 w-full text-white font-medium"
                                        value={t.title}
                                        onChange={(e) =>
                                            updateTaskField(
                                                i,
                                                "title",
                                                e.target.value,
                                            )
                                        }
                                    />
                                </td>
                                <td className="px-4 py-2">
                                    <input
                                        className="bg-transparent border-none outline-none focus:ring-1 focus:ring-indigo-500 rounded px-1 w-full text-gray-400 text-xs"
                                        value={t.description}
                                        onChange={(e) =>
                                            updateTaskField(
                                                i,
                                                "description",
                                                e.target.value,
                                            )
                                        }
                                    />
                                </td>
                                <td className="px-4 py-2 text-center">
                                    <input
                                        type="number"
                                        className="bg-transparent border-none outline-none focus:ring-1 focus:ring-indigo-500 rounded px-1 w-full text-indigo-300 font-bold"
                                        value={t.story_point}
                                        onChange={(e) =>
                                            updateTaskField(
                                                i,
                                                "story_point",
                                                parseInt(e.target.value) || 0,
                                            )
                                        }
                                    />
                                </td>
                                <td className="px-4 py-2">
                                    <select
                                        value={t.priority}
                                        onChange={(e) =>
                                            updateTaskField(
                                                i,
                                                "priority",
                                                e.target.value,
                                            )
                                        }
                                        className={`bg-transparent outline-none rounded px-1 font-semibold ${PRIORITY_COLOR[t.priority] ?? ""}`}
                                    >
                                        <option
                                            value="High"
                                            className="bg-gray-900 text-red-400"
                                        >
                                            High
                                        </option>
                                        <option
                                            value="Medium"
                                            className="bg-gray-900 text-yellow-400"
                                        >
                                            Medium
                                        </option>
                                        <option
                                            value="Low"
                                            className="bg-gray-900 text-green-400"
                                        >
                                            Low
                                        </option>
                                    </select>
                                </td>
                                <td className="px-4 py-2">
                                    <input
                                        className="bg-transparent border-none outline-none focus:ring-1 focus:ring-indigo-500 rounded px-1 w-full text-gray-400"
                                        value={t.assignee_suggestion}
                                        onChange={(e) =>
                                            updateTaskField(
                                                i,
                                                "assignee_suggestion",
                                                e.target.value,
                                            )
                                        }
                                    />
                                </td>
                                <td className="px-4 py-2">
                                    <button
                                        onClick={() => removeTask(i)}
                                        className="opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-500 transition-all"
                                    >
                                        ✕
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
