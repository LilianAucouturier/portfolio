"use client";

import { useState } from "react";
import { createClient } from "@/utils/supabase/client";
import { useRouter } from "next/navigation";
import { Mail, Lock, ArrowRight, Loader2 } from "lucide-react";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [useMagicLink, setUseMagicLink] = useState(true);
    const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

    const router = useRouter();
    const supabase = createClient();

    const handleMagicLinkLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setMessage(null);

        const { error } = await supabase.auth.signInWithOtp({
            email,
            options: {
                emailRedirectTo: `${window.location.origin}/auth/callback`,
            },
        });

        setLoading(false);

        if (error) {
            setMessage({ type: "error", text: error.message });
        } else {
            setMessage({
                type: "success",
                text: "Vérifiez votre email ! Un lien de connexion vous a été envoyé.",
            });
        }
    };

    const handlePasswordLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setMessage(null);

        const { error } = await supabase.auth.signInWithPassword({
            email,
            password,
        });

        setLoading(false);

        if (error) {
            setMessage({ type: "error", text: error.message });
        } else {
            router.push("/");
            router.refresh();
        }
    };

    const handleSignUp = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setMessage(null);

        const { error } = await supabase.auth.signUp({
            email,
            password,
            options: {
                emailRedirectTo: `${window.location.origin}/auth/callback`,
            },
        });

        setLoading(false);

        if (error) {
            setMessage({ type: "error", text: error.message });
        } else {
            setMessage({
                type: "success",
                text: "Compte créé ! Vérifiez votre email pour confirmer.",
            });
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-6 bg-zinc-950">
            <div className="w-full max-w-md">
                {/* Logo/Header */}
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-emerald-400 to-teal-500 text-transparent bg-clip-text">
                        Cortex Run
                    </h1>
                    <p className="text-zinc-400">Votre coach running IA</p>
                </div>

                {/* Card */}
                <div className="bg-zinc-900 rounded-2xl p-8 border border-zinc-800">
                    {/* Tabs */}
                    <div className="flex gap-2 mb-6 bg-zinc-800 rounded-lg p-1">
                        <button
                            onClick={() => setUseMagicLink(true)}
                            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${useMagicLink
                                    ? "bg-emerald-500 text-white"
                                    : "text-zinc-400 hover:text-white"
                                }`}
                        >
                            Magic Link
                        </button>
                        <button
                            onClick={() => setUseMagicLink(false)}
                            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${!useMagicLink
                                    ? "bg-emerald-500 text-white"
                                    : "text-zinc-400 hover:text-white"
                                }`}
                        >
                            Email/Password
                        </button>
                    </div>

                    {/* Magic Link Form */}
                    {useMagicLink ? (
                        <form onSubmit={handleMagicLinkLogin} className="space-y-4">
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium text-zinc-300 mb-2">
                                    Email
                                </label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={20} />
                                    <input
                                        id="email"
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        placeholder="vous@exemple.com"
                                        required
                                        className="w-full pl-11 pr-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full bg-emerald-500 hover:bg-emerald-600 disabled:bg-zinc-700 disabled:text-zinc-500 text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="animate-spin" size={20} />
                                        Envoi en cours...
                                    </>
                                ) : (
                                    <>
                                        Envoyer le Magic Link
                                        <ArrowRight size={20} />
                                    </>
                                )}
                            </button>
                        </form>
                    ) : (
                        /* Password Form */
                        <form onSubmit={handlePasswordLogin} className="space-y-4">
                            <div>
                                <label htmlFor="email-pwd" className="block text-sm font-medium text-zinc-300 mb-2">
                                    Email
                                </label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={20} />
                                    <input
                                        id="email-pwd"
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        placeholder="vous@exemple.com"
                                        required
                                        className="w-full pl-11 pr-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                                    />
                                </div>
                            </div>

                            <div>
                                <label htmlFor="password" className="block text-sm font-medium text-zinc-300 mb-2">
                                    Mot de passe
                                </label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={20} />
                                    <input
                                        id="password"
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder="••••••••"
                                        required
                                        className="w-full pl-11 pr-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                                    />
                                </div>
                            </div>

                            <div className="flex gap-2">
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="flex-1 bg-emerald-500 hover:bg-emerald-600 disabled:bg-zinc-700 disabled:text-zinc-500 text-white font-semibold py-3 rounded-lg transition-colors"
                                >
                                    {loading ? (
                                        <Loader2 className="animate-spin mx-auto" size={20} />
                                    ) : (
                                        "Se connecter"
                                    )}
                                </button>
                                <button
                                    type="button"
                                    onClick={handleSignUp}
                                    disabled={loading}
                                    className="flex-1 bg-zinc-700 hover:bg-zinc-600 disabled:bg-zinc-800 disabled:text-zinc-600 text-white font-semibold py-3 rounded-lg transition-colors"
                                >
                                    S'inscrire
                                </button>
                            </div>
                        </form>
                    )}

                    {/* Message */}
                    {message && (
                        <div
                            className={`mt-4 p-3 rounded-lg text-sm ${message.type === "success"
                                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                    : "bg-red-500/10 text-red-400 border border-red-500/20"
                                }`}
                        >
                            {message.text}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <p className="text-center text-zinc-500 text-sm mt-6">
                    En continuant, vous acceptez nos conditions d'utilisation
                </p>
            </div>
        </div>
    );
}
