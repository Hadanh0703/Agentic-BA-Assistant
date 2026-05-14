import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { projectsApi } from "@/lib/api";
import axios from "axios";

export function useProjects() {
    const [projects, setProjects] = useState<any[]>([]);
    const { data: session } = useSession();
    const email = session?.user?.email;

    useEffect(() => {
        if (!email) return;
        axios
            .post(`${process.env.NEXT_PUBLIC_API_URL}/users/me/upsert`, {
                email: email,
                name: session?.user?.name,
                avatar: session?.user?.image,
            })
            .catch(() => {});
    }, [email]);

    const fetchProjects = async () => {
        if (!email) return;
        const res = await projectsApi.list(email);
        setProjects(res.data);
    };

    useEffect(() => {
        fetchProjects();
    }, [email]);

    const createProject = async (name: string) => {
        await projectsApi.create(name, email);
        await fetchProjects();
    };

    const deleteProject = async (id: number) => {
        await projectsApi.delete(id);
        await fetchProjects();
    };

    return { projects, createProject, deleteProject, refetch: fetchProjects };
}
