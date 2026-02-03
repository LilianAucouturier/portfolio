import { createClient } from "@/utils/supabase/server";
import { redirect } from "next/navigation";
import PlanDashboard from "@/components/PlanDashboard";
import { Sparkles } from "lucide-react";
import Link from "next/link";

export default async function ProgramPage() {
    const supabase = await createClient();

    // Check authentication
    const {
        data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
        redirect("/login");
    }

    // Fetch active training plan
    const { data: activePlan, error: planError } = await supabase
        .from("training_plans")
        .select("*")
        .eq("user_id", user.id)
        .eq("status", "active")
        .order("created_at", { ascending: false })
        .limit(1)
        .single();

    // No active plan - show create CTA
    if (planError || !activePlan) {
        return (
            <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">Mon Programme</h1>
                        <p className="text-zinc-400">
                            Votre plan d'entraînement personnalisé
                        </p>
                    </div>
                </div>

                {/* No Plan CTA */}
                <div className="bg-zinc-900 rounded-2xl p-8 text-center">
                    <div className="mb-6">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 mb-4">
                            <Sparkles className="text-emerald-500" size={32} />
                        </div>
                        <h2 className="text-xl font-bold mb-2">
                            Aucun plan d'entraînement actif
                        </h2>
                        <p className="text-zinc-400 mb-6 max-w-md mx-auto">
                            Laissez l'IA créer un plan personnalisé basé sur vos objectifs,
                            votre niveau et vos données de récupération.
                        </p>
                    </div>

                    <Link
                        href="/program/create"
                        className="inline-flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white px-8 py-4 rounded-xl font-semibold transition-all"
                    >
                        <Sparkles size={20} />
                        Générer mon plan IA
                    </Link>

                    <p className="text-xs text-zinc-500 mt-4">
                        Durée : 4 semaines · Basé sur vos métriques HRV et sommeil
                    </p>
                </div>

                {/* Info Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                    <div className="bg-zinc-900 rounded-xl p-4">
                        <p className="text-lg font-bold mb-1">📊</p>
                        <p className="text-sm font-semibold mb-1">Analyse de vos données</p>
                        <p className="text-xs text-zinc-500">
                            HRV, sommeil et fatigue des 7 derniers jours
                        </p>
                    </div>

                    <div className="bg-zinc-900 rounded-xl p-4">
                        <p className="text-lg font-bold mb-1">📚</p>
                        <p className="text-sm font-semibold mb-1">
                            Basé sur la science
                        </p>
                        <p className="text-xs text-zinc-500">
                            Périodisation, VMA, seuil lactique
                        </p>
                    </div>

                    <div className="bg-zinc-900 rounded-xl p-4">
                        <p className="text-lg font-bold mb-1">🎯</p>
                        <p className="text-sm font-semibold mb-1">Personnalisé</p>
                        <p className="text-xs text-zinc-500">
                            Adapté à votre objectif et votre forme actuelle
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    // Fetch training sessions for this plan
    const { data: sessions, error: sessionsError } = await supabase
        .from("training_sessions")
        .select("*")
        .eq("plan_id", activePlan.id)
        .order("date", { ascending: true });

    if (sessionsError || !sessions) {
        return (
            <div className="p-6">
                <h1 className="text-3xl font-bold mb-4">Mon Programme</h1>
                <p className="text-red-400">
                    Erreur lors du chargement des séances : {sessionsError?.message}
                </p>
            </div>
        );
    }

    return (
        <div className="p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-3xl font-bold mb-2">Mon Programme</h1>
                    <p className="text-zinc-400">
                        Plan actif depuis le{" "}
                        {new Date(activePlan.start_date).toLocaleDateString("fr-FR")}
                    </p>
                </div>

                <Link
                    href="/program/create"
                    className="text-sm text-emerald-500 hover:text-emerald-400 transition-colors"
                >
                    + Nouveau plan
                </Link>
            </div>

            {/* Plan Dashboard */}
            <PlanDashboard plan={activePlan} sessions={sessions} />
        </div>
    );
}
