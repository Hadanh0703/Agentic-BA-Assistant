const AGENT_LABELS: Record<string, string> = {
    interviewer: "Interviewer",
    standardizer: "Standardizer",
    architect: "Architect",
    risk_observer: "Risk Observer",
};

export default function AgentStatusBar({
    step,
    message,
}: {
    step: string;
    message: string;
}) {
    return (
        <div className="flex items-center gap-3 bg-indigo-950 border border-indigo-700 rounded-lg px-4 py-2 text-xl">
            <span className="animate-spin text-indigo-400">⟳</span>
            <span className="text-indigo-300 font-semibold">
                {AGENT_LABELS[step] ?? step}
            </span>
            <span className="text-gray-400">{message}</span>
        </div>
    );
}
