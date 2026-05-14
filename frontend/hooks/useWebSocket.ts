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

        ws.current = new WebSocket(`ws://localhost:8000/ws/${projectId}`);

        ws.current.onopen = () => setIsConnected(true);
        ws.current.onclose = () => setIsConnected(false);

        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === "agent_status") {
                setAgentStatus({ step: data.step, message: data.message });
            }
        };

        return () => {
            ws.current?.close();
        };
    }, [projectId]);

    const clearStatus = () => setAgentStatus(null);

    return { agentStatus, isConnected, clearStatus };
}
