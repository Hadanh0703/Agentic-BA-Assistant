export default function RiskReport({ report }: { report: any }) {
    if (!report) return null;

    const riskList = report.red_flags || report.risks || [];
    const isSafe = report.is_safe ?? true;

    return (
        <div
            className={`rounded-xl border p-5 space-y-3 ${
                isSafe
                    ? "border-green-700 bg-green-950/30"
                    : "border-red-700 bg-red-950/30"
            }`}
        >
            <div className="flex items-center gap-2">
                <span className="text-2xl">{isSafe ? "✅" : "⚠️"}</span>
                <h3 className="font-bold text-lg text-white">
                    {isSafe ? "Risk Report: Safe" : "Risk Report: Warning"}
                </h3>
            </div>

            {riskList.length > 0 && (
                <div>
                    <p className="text-red-400 font-semibold mb-1">
                        Red Flags / Risks:
                    </p>
                    <ul className="space-y-1">
                        {riskList.map((f: string, i: number) => (
                            <li
                                key={i}
                                className="text-red-300 text-sm flex gap-2"
                            >
                                <span className="font-bold">•</span>
                                <span>{f}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            <div>
                <p className="text-gray-400 font-semibold mb-1">Khuyến nghị:</p>
                <p className="text-gray-300 text-sm leading-relaxed">
                    {report.recommendations || "Không có khuyến nghị cụ thể."}
                </p>
            </div>
        </div>
    );
}
