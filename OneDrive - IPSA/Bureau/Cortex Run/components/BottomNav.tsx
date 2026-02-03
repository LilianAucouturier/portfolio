"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Calendar, Bot, User } from "lucide-react";

const navItems = [
    { href: "/", icon: Home, label: "Accueil" },
    { href: "/program", icon: Calendar, label: "Programme" },
    { href: "/coach", icon: Bot, label: "Coach" },
    { href: "/profile", icon: User, label: "Profil" },
];

export default function BottomNav() {
    const pathname = usePathname();

    return (
        <nav className="fixed bottom-0 left-0 right-0 bg-zinc-900/95 backdrop-blur-lg border-t border-zinc-800 z-50">
            <div className="flex justify-around items-center h-16 px-2">
                {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    const Icon = item.icon;

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex flex-col items-center justify-center w-full h-full transition-colors ${isActive
                                    ? "text-emerald-500"
                                    : "text-zinc-400 hover:text-zinc-200"
                                }`}
                        >
                            <Icon size={24} strokeWidth={2} />
                            <span className="text-xs mt-1 font-medium">{item.label}</span>
                        </Link>
                    );
                })}
            </div>
        </nav>
    );
}
