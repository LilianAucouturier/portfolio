import { createClient } from "@/utils/supabase/server";
import { redirect } from "next/navigation";
import { Activity, Heart, TrendingUp } from "lucide-react";

export default async function Home() {
    const supabase = await createClient();

    // Vérifier l'authentification
    const {
        data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
        redirect("/login");
    }

    // Récupérer les métriques des 7 derniers jours
    const today = new Date().toISOString().split("T")[0];
    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
        .toISOString()
        .split("T")[0];

    const { data: metrics, error } = await supabase
        .from("daily_metrics")
        .select("*")
        .eq("user_id", user.id)
        .gte("date", sevenDaysAgo)
        .order("date", { ascending: false });

    // Métriques du jour (ou dernières disponibles)
    const todayMetrics = metrics?.find((m) => m.date === today);
    const latestMetrics = metrics?.[0]; // Plus récente
    const displayMetrics = todayMetrics || latestMetrics;

    // Calculer les moyennes sur 7 jours
    const avgHRV =
        metrics && metrics.length > 0
            ? Math.round(
                metrics.reduce((sum, m) => sum + (m.hrv_ms || 0), 0) / metrics.length
            )
            : null;

    const avgSleep =
        metrics && metrics.length > 0
            ? (
                metrics.reduce((sum, m) => sum + (m.sleep_duration_hours || 0), 0) /
                metrics.length
            ).toFixed(1)
            : null;

    // Calculer le score de forme (basé sur HRV et sommeil)
    let fitnessScore = 5;
    if (displayMetrics) {
        const hrvScore = displayMetrics.hrv_ms
            ? Math.min(10, Math.round(displayMetrics.hrv_ms / 10))
            : 5;
        const sleepScore = displayMetrics.sleep_duration_hours
            ? Math.min(10, Math.round(displayMetrics.sleep_duration_hours * 1.3))
            : 5;
        fitnessScore = Math.round((hrvScore + sleepScore) / 2);
    }

    // Nombre de séances (placeholder - à calculer depuis activities)
    const sessionsCount = 12;

    return (
        <div className="p-6">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-2">
                    Bonjour, {user.email?.split("@")[0]} 🏃
                </h1>
                <p className="text-zinc-400">
                    {displayMetrics
                        ? displayMetrics.date === today
                            ? "Données d'aujourd'hui synchronisées"
                            : `Dernière sync : ${new Date(displayMetrics.date).toLocaleDateString("fr-FR")}`
                        : "En attente de synchronisation..."}
                </p>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-3 gap-4 mb-8">
                <StatCard
                    icon={<Activity size={20} />}
                    label="Séances"
                    value={sessionsCount.toString()}
                    trend="+2"
                />
                <StatCard
                    icon={<Heart size={20} />}
                    label="HRV"
                    value={displayMetrics?.hrv_ms ? `${displayMetrics.hrv_ms}ms` : "—"}
                    trend={
                        displayMetrics?.hrv_ms && avgHRV
                            ? displayMetrics.hrv_ms >= avgHRV
                                ? "↑"
                                : "↓"
                            : "—"
                    }
                />
                <StatCard
                    icon={<TrendingUp size={20} />}
                    label="Forme"
                    value={`${fitnessScore}/10`}
                    trend={fitnessScore >= 7 ? "Bon" : fitnessScore >= 5 ? "OK" : "Fatigué"}
                />
            </div>

            {/* Sommeil Card */}
            {displayMetrics?.sleep_duration_hours && (
                <div className="bg-zinc-900 rounded-xl p-6 mb-6">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-lg font-semibold">Sommeil</h3>
                        <span className="text-2xl">😴</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-bold">
                            {displayMetrics.sleep_duration_hours.toFixed(1)}h
                        </span>
                        <span className="text-zinc-500">
                            {displayMetrics.date === today ? "cette nuit" : "dernière mesure"}
                        </span>
                    </div>
                    {avgSleep && (
                        <p className="text-sm text-zinc-400 mt-2">
                            Moyenne 7j : {avgSleep}h
                        </p>
                    )}
                </div>
            )}

            {/* Prochaine séance */}
            <div className="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl p-6 mb-6">
                <p className="text-sm text-emerald-100 mb-2">Aujourd'hui</p>
                <h2 className="text-2xl font-bold mb-1">Endurance Facile</h2>
                <p className="text-emerald-100 mb-4">8 km · Zone 2 · 50 min</p>
                <button className="bg-white text-emerald-600 px-6 py-2 rounded-lg font-semibold hover:bg-emerald-50 transition-colors">
                    Démarrer
                </button>
            </div>

            {/* Métriques détaillées */}
            {displayMetrics && (
                <div className="bg-zinc-900 rounded-xl p-6 mb-6">
                    <h3 className="text-lg font-semibold mb-4">Métriques détaillées</h3>
                    <div className="grid grid-cols-2 gap-4">
                        <MetricRow
                            label="FC Repos"
                            value={
                                displayMetrics.resting_hr
                                    ? `${displayMetrics.resting_hr} bpm`
                                    : "—"
                            }
                        />
                        <MetricRow
                            label="Pas"
                            value={
                                displayMetrics.steps
                                    ? displayMetrics.steps.toLocaleString("fr-FR")
                                    : "—"
                            }
                        />
                        <MetricRow
                            label="Calories"
                            value={
                                displayMetrics.active_calories
                                    ? `${displayMetrics.active_calories} kcal`
                                    : "—"
                            }
                        />
                        <MetricRow
                            label="Fatigue"
                            value={
                                displayMetrics.fatigue_score
                                    ? `${displayMetrics.fatigue_score}/10`
                                    : "Non renseigné"
                            }
                        />
                    </div>
                </div>
            )}

            {/* Message si pas de données */}
            {!displayMetrics && (
                <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-6 mb-6">
                    <h3 className="text-amber-400 font-semibold mb-2">
                        📊 En attente de données
                    </h3>
                    <p className="text-amber-200/80 text-sm">
                        Lancez votre Raccourci iOS "Cortex Sync" pour synchroniser vos
                        métriques Apple Health.
                    </p>
                </div>
            )}

            {/* Placeholder sections */}
            <div className="space-y-4">
                <SectionPlaceholder title="Historique récent" />
                <SectionPlaceholder title="Objectif Marathon" />
            </div>
        </div>
    );
}

function StatCard({
    icon,
    label,
    value,
    trend,
}: {
    icon: React.ReactNode;
    label: string;
    value: string;
    trend: string;
}) {
    return (
        <div className="bg-zinc-900 rounded-xl p-4">
            <div className="text-zinc-400 mb-2">{icon}</div>
            <div className="text-xs text-zinc-500 mb-1">{label}</div>
            <div className="text-lg font-bold">{value}</div>
            <div className="text-xs text-emerald-500">{trend}</div>
        </div>
    );
}

function MetricRow({ label, value }: { label: string; value: string }) {
    return (
        <div>
            <p className="text-xs text-zinc-500 mb-1">{label}</p>
            <p className="text-white font-medium">{value}</p>
        </div>
    );
}

function SectionPlaceholder({ title }: { title: string }) {
    return (
        <div className="bg-zinc-900 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-2">{title}</h3>
            <p className="text-zinc-500">À venir...</p>
        </div>
    );
}
