import { auth } from "@/auth";
import { redirect } from "next/navigation";
import Sidebar from "@/components/Sidebar";

export default async function ProjectsPage() {
    const session = await auth();
    if (!session) redirect("/login");

    return (
        <div className="flex h-screen bg-gray-950">
            <Sidebar />
            <main className="flex-1 flex items-center justify-center text-gray-500">
                <div className="text-center">
                    <p className="text-4xl mb-3">👈</p>
                    <p className="text-lg font-medium">
                        Chọn project từ sidebar
                    </p>
                    <p className="text-sm mt-1">hoặc tạo project mới</p>
                </div>
            </main>
        </div>
    );
}
