import axios from "axios";

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL,
});

export const projectsApi = {
    list: (email?: string) =>
        api.get("/projects", { params: { user_email: email } }),
    create: (name: string, email?: string) =>
        api.post("/projects", { name, user_email: email }),
    delete: (id: number) => api.delete(`/projects/${id}`),
    getMessages: (id: number) => api.get(`/projects/${id}/messages`),
    getArtifacts: (id: number) => api.get(`/projects/${id}/artifacts`),
    uploadFile: (id: number, formData: FormData) =>
        api.post(`/ingest/${id}`, formData, {
            headers: { "Content-Type": "multipart/form-data" },
        }),

    deleteFile: (projectId: number, fileName: string) =>
        api.delete(`/projects/${projectId}/files/${fileName}`),
    getFiles: (projectId: number) => api.get(`/projects/${projectId}/files`),
    updateArtifact: (artifactId: number, data: any) =>
        api.put(`/artifacts/${artifactId}`, data),
    deleteArtifact: (projectId: number, artifactId: number) =>
        api.delete(`/projects/${projectId}/artifacts/${artifactId}`),
};

export const chatApi = {
    send: (projectId: number, userInput: string, history: string) =>
        api.post("/chat", {
            project_id: projectId,
            user_input: userInput,
            history,
        }),
    confirm: (
        projectId: number,
        userStory: {
            title: string;
            role: string;
            action: string;
            benefit: string;
            acceptance_criteria: string[];
        },
    ) =>
        api.post("/confirm", {
            project_id: projectId,
            user_story: userStory,
        }),
};
