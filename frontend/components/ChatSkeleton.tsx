export default function ChatSkeleton() {
    return (
        <div className="flex flex-col h-screen bg-gray-950 p-6 space-y-4 animate-pulse">
            <div className="flex justify-start">
                <div className="bg-gray-800 rounded-xl h-12 w-80" />
            </div>
            <div className="flex justify-end">
                <div className="bg-indigo-900 rounded-xl h-10 w-56" />
            </div>
            <div className="flex justify-start">
                <div className="bg-gray-800 rounded-xl h-20 w-96" />
            </div>
            <div className="flex justify-end">
                <div className="bg-indigo-900 rounded-xl h-10 w-40" />
            </div>
            <div className="mt-6 bg-gray-800 rounded-xl h-48 w-full" />
        </div>
    );
}
