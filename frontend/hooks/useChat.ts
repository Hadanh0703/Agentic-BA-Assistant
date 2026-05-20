"use client";
import { useState, useEffect, useCallback } from "react";
import { chatApi, projectsApi } from "@/lib/api";

export type Message = {
    role: "user" | "agent";
    content: string;
    agent_name?: string;
};

export interface TaskGroup {
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

export function useChat(projectId: number) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [history, setHistory] = useState("");
    const [pendingStory, setPendingStory] = useState<any | null>(null);
    const [tasks, setTasks] = useState<TaskGroup[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isLoadingHistory, setIsLoadingHistory] = useState(false);
    const [justFinishedConfirm, setJustFinishedConfirm] = useState(false);

    const loadProjectData = useCallback(async () => {
        if (!projectId || isNaN(projectId)) return;

        setIsLoadingHistory(true);
        try {
            const [msgRes, artRes] = await Promise.all([
                projectsApi.getMessages(projectId).catch(() => ({ data: [] })),
                projectsApi.getArtifacts(projectId).catch(() => ({ data: [] })),
            ]);

            setMessages(
                msgRes.data.map((m: any) => ({
                    role: m.role,
                    content: m.content,
                    agent_name: m.agent_name,
                })),
            );

            const artifacts: any[] = artRes.data;

            const allTaskGroups: TaskGroup[] = artifacts
                .filter((a) => a.type === "task_list")
                .map((a) => ({
                    id: a.id,
                    story_details: a.data.story_details,
                    items: a.data.tasks || [],
                    risk_report: a.data.risk_report || null,
                    created_at: a.created_at,
                }));

            setTasks(allTaskGroups);

            const lastTaskList = [...artifacts]
                .reverse()
                .find((a) => a.type === "task_list");
            const lastUserStory = [...artifacts]
                .reverse()
                .find((a) => a.type === "user_story");

            if (
                lastUserStory &&
                (!lastTaskList || lastUserStory.id > lastTaskList.id)
            ) {
                setPendingStory(lastUserStory.data);
            } else {
                setPendingStory(null);
            }
        } catch (err) {
            console.error("Lỗi tải dữ liệu project:", err);
        } finally {
            setIsLoadingHistory(false);
        }
    }, [projectId]);

    useEffect(() => {
        loadProjectData();
    }, [loadProjectData]);

    const sendMessage = async (input: string) => {
        setMessages((prev) => [...prev, { role: "user", content: input }]);
        setIsLoading(true);
        try {
            const res = await chatApi.send(projectId, input, history);
            const data = res.data;
            if (data.status === "need_more_info") {
                setMessages((prev) => [
                    ...prev,
                    {
                        role: "agent",
                        content: data.feedback,
                        agent_name: "Interviewer",
                    },
                ]);
                setHistory((h) => `${h}\nUser: ${input}\nAI: ${data.feedback}`);
            } else if (data.status === "general_response") {
                setMessages((prev) => [
                    ...prev,
                    {
                        role: "agent",
                        content: data.response,
                        agent_name: "Assistant",
                    },
                ]);
                setHistory((h) => `${h}\nUser: ${input}\nAI: ${data.response}`);
            } else if (data.status === "awaiting_confirmation") {
                setPendingStory(data.user_story);
                setMessages((prev) => [
                    ...prev,
                    {
                        role: "agent",
                        content:
                            "Tôi đã soạn xong User Story. Vui lòng xem xét và xác nhận!",
                        agent_name: "Standardizer",
                    },
                ]);
                setHistory("");
            }
        } finally {
            setIsLoading(false);
        }
    };

    const confirmStory = async (editedStory: any) => {
        setIsLoading(true);
        try {
            const formattedStory = {
                title: editedStory.title || "User Story",
                role: editedStory.role || "",
                action: editedStory.action || "",
                benefit: editedStory.benefit || "",
                acceptance_criteria: Array.isArray(
                    editedStory.acceptance_criteria,
                )
                    ? editedStory.acceptance_criteria
                    : [],
            };

            const res = await chatApi.confirm(projectId, formattedStory);

            if (res.data) {
                setPendingStory(null);
                await loadProjectData();
                setJustFinishedConfirm(true);
            }
        } catch (err: any) {
            console.error("Lỗi 422:", err.response?.data);
            alert(
                "Lỗi xác nhận: " + JSON.stringify(err.response?.data?.detail),
            );
        } finally {
            setIsLoading(false);
        }
    };

    const deleteStory = async (artifactId: number) => {
        try {
            await projectsApi.deleteArtifact(projectId, artifactId);
            setTasks((prev) => prev.filter((t) => t.id !== artifactId));
        } catch (err) {
            console.error("Lỗi khi xóa story:", err);
            alert("Không thể xóa story này!");
        }
    };

    return {
        messages,
        pendingStory,
        tasks,
        isLoading,
        isLoadingHistory,
        justFinishedConfirm,
        setJustFinishedConfirm,
        sendMessage,
        confirmStory,
        deleteStory,
    };
}
