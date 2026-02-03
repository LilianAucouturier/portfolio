import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import BottomNav from "@/components/BottomNav";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "Cortex Run - AI Running Coach",
    description: "Votre coach running personnel propulsé par l'IA",
    manifest: "/manifest.json",
    themeColor: "#10b981",
    appleWebApp: {
        capable: true,
        statusBarStyle: "black-translucent",
        title: "Cortex Run",
    },
    viewport: {
        width: "device-width",
        initialScale: 1,
        maximumScale: 1,
        userScalable: false,
    },
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="fr">
            <head>
                <link rel="apple-touch-icon" href="/icon-192.png" />
            </head>
            <body className={`${inter.className} bg-zinc-950 text-white`}>
                {/* Container avec padding bottom pour la nav */}
                <main className="min-h-screen pb-20">
                    {children}
                </main>

                {/* Barre de navigation fixe en bas */}
                <BottomNav />
            </body>
        </html>
    );
}
