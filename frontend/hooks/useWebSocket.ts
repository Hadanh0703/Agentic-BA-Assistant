import { useEffect, useRef, useState } from "react";

export type AgentStatus = {
    step: string;
    message: string;
};

export function useWebSocket(projectId: number | null) {
    const ws = useRef<WebSocket | null>(null);
    const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        if (!projectId) return;

        const apiUrl =
            process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const wsUrl = apiUrl.replace(/^http/, "ws") + `/ws/${projectId}`;

        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => {
            console.log("WebSocket Connected");
            setIsConnected(true);
        };

        ws.current.onclose = () => {
            console.log("WebSocket Disconnected");
            setIsConnected(false);
        };

        ws.current.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === "agent_status") {
                    setAgentStatus({ step: data.step, message: data.message });
                }
            } catch (error) {
                console.error("Lỗi parse dữ liệu WebSocket:", error);
            }
        };

        return () => {
            ws.current?.close();
        };
    }, [projectId]);

    const clearStatus = () => setAgentStatus(null);

    return { agentStatus, isConnected, clearStatus };
}
