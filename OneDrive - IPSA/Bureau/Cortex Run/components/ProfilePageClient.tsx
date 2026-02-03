"use client";

import { useState } from "react";
import { syncStravaActivities } from "@/app/actions/sync-strava";
import { useRouter, useSearchParams } from "next/navigation";
import { RefreshCw, ExternalLink, CheckCircle, XCircle } from "lucide-react";

interface ProfilePageClientProps {
    user: any;
    stravaConnected: boolean;
    stravaLastSync: string | null;
}

export default function ProfilePageClient({
    user,
    stravaConnected,
    stravaLastSync,
}: ProfilePageClientProps) {
    const [syncing, setSyncing] = useState(false);
    const [syncResult, setSyncResult] = useState<{
        type: "success" | "error";
        message: string;
    } | null>(null);
    const router = useRouter();
    const searchParams = useSearchParams();

    const stravaConnectedParam = searchParams.get("strava_connected");
    const stravaErrorParam = searchParams.get("strava_error");

    const handleSync = async () => {
        setSyncing(true);
        setSyncResult(null);

        const result = await syncStravaActivities();

        if (result.success) {
            setSyncResult({
                type: "success",
                message: result.message || "Synchronisation réussie",
            });
            router.refresh();
        } else {
            setSyncResult({
                type: "error",
                message: result.error || "Erreur de synchronisation",
            });
        }

        setSyncing(false);
    };

    return (
        <div className="p-6">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-2">Profil</h1>
                <p className="text-zinc-400">{user.email}</p>
            </div>

            {/* Connection Success Banner */}
            {stravaConnectedParam === "true" && (
                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 mb-6">
                    <div className="flex items-start gap-3">
                        <CheckCircle className="text-emerald-400 flex-shrink-0" size={24} />
                        <div>
                            <h4 className="text-emerald-400 font-semibold mb-1">
                                Strava connecté avec succès !
                            </h4>
                            <p className="text-emerald-200/80 text-sm">
                                Vous pouvez maintenant synchroniser vos activités.
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Connection Error Banner */}
            {stravaErrorParam && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-6">
                    <div className="flex items-start gap-3">
                        <XCircle className="text-red-400 flex-shrink-0" size={24} />
                        <div>
                            <h4 className="text-red-400 font-semibold mb-1">
                                Erreur de connexion Strava
                            </h4>
                            <p className="text-red-200/80 text-sm">
                                {stravaErrorParam === "access_denied"
                                    ? "Vous avez refusé l'accès à Strava."
                                    : "Une erreur est survenue. Veuillez réessayer."}
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Strava Connection Section */}
            <div className="bg-zinc-900 rounded-xl p-6 mb-6">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h3 className="text-lg font-semibold mb-1 flex items-center gap-2">
                            <span className="text-2xl">🏃</span>
                            Strava
                        </h3>
                        <p className="text-sm text-zinc-400">
                            Synchronisez vos activités de course
                        </p>
                    </div>

                    {stravaConnected ? (
                        <div className="flex items-center gap-2 text-emerald-500 text-sm">
                            <CheckCircle size={16} />
                            <span>Connecté</span>
                        </div>
                    ) : (
                        <div className="flex items-center gap-2 text-zinc-500 text-sm">
                            <XCircle size={16} />
                            <span>Non connecté</span>
                        </div>
                    )}
                </div>

                {!stravaConnected ? (
                    /* Connect Button */
                    <a
                        href="/auth/strava"
                        className="inline-flex items-center gap-2 bg-[#FC4C02] hover:bg-[#E34402] text-white px-6 py-3 rounded-lg font-semibold transition-colors"
                    >
                        <ExternalLink size={20} />
                        Connecter Strava
                    </a>
                ) : (
                    /* Sync Section */
                    <div>
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                {stravaLastSync ? (
                                    <p className="text-sm text-zinc-400">
                                        Dernière synchronisation :{" "}
                                        {new Date(stravaLastSync).toLocaleString("fr-FR")}
                                    </p>
                                ) : (
                                    <p className="text-sm text-zinc-400">
                                        Jamais synchronisé
                                    </p>
                                )}
                            </div>
                        </div>

                        <button
                            onClick={handleSync}
                            disabled={syncing}
                            className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 disabled:bg-zinc-700 disabled:text-zinc-500 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
                        >
                            <RefreshCw
                                size={20}
                                className={syncing ? "animate-spin" : ""}
                            />
                            {syncing ? "Synchronisation..." : "Synchroniser maintenant"}
                        </button>

                        {syncResult && (
                            <div
                                className={`mt-4 p-3 rounded-lg text-sm ${syncResult.type === "success"
                                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                        : "bg-red-500/10 text-red-400 border border-red-500/20"
                                    }`}
                            >
                                {syncResult.message}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* User Info Section */}
            <div className="space-y-4">
                <div className="bg-zinc-900 rounded-xl p-6">
                    <h3 className="text-lg font-semibold mb-4">Informations personnelles</h3>
                    <div className="space-y-3">
                        <div>
                            <p className="text-xs text-zinc-500 mb-1">Email</p>
                            <p className="text-white">{user.email}</p>
                        </div>
                        <div>
                            <p className="text-xs text-zinc-500 mb-1">User ID</p>
                            <p className="text-zinc-400 font-mono text-xs">{user.id}</p>
                        </div>
                    </div>
                </div>

                {/* Logout (future) */}
                <div className="bg-zinc-900 rounded-xl p-6">
                    <h3 className="text-lg font-semibold mb-4">Paramètres</h3>
                    <button className="text-sm text-red-400 hover:text-red-300 transition-colors">
                        Se déconnecter
                    </button>
                </div>
            </div>
        </div>
    );
}
