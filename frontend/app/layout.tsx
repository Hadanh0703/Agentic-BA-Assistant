import type { Metadata } from "next";
import { SessionProvider } from "next-auth/react";
import { auth } from "@/auth";
import "./globals.css";

export const metadata: Metadata = {
    title: "AI-BA Assistant",
};

export default async function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const session = await auth();

    return (
        <html lang="vi">
            <body>
                <SessionProvider session={session}>{children}</SessionProvider>
            </body>
        </html>
    );
}
