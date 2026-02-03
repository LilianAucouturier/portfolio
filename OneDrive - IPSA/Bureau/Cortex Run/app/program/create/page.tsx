"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { generateTrainingPlan } from "@/app/actions/generate-plan";
import { createClient } from "@/utils/supabase/client";
import { Sparkles, Loader2, Brain, CheckCircle, XCircle } from "lucide-react";

export default function CreatePlanPage() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);
    const router = useRouter();
    const supabase = createClient();

    const handleGenerate = async () => {
        setLoading(true);
        setError(null);
        setSuccess(false);

        try {
            // Récupérer l'utilisateur connecté
            const {
                data: { user },
            } = await supabase.auth.getUser();

            if (!user) {
                throw new Error("Vous devez être connecté");
            }

            // Appeler la Server Action
            const result = await generateTrainingPlan(user.id);

            if (result.success) {
                setSuccess(true);
                // Redirection après 2 secondes
                setTimeout(() => {
                    router.push("/program");
                }, 2000);
            } else {
                setError(result.error || "Erreur inconnue");
            }
        } catch (err: any) {
            setError(err.message || "Une erreur s'est produite");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
                    <Brain className="text-emerald-500" size={32} />
                    Générer mon Plan IA
                </h1>
                <p className="text-zinc-400">
                    L'IA va analyser vos métriques, vos objectifs et les dernières
                    recherches scientifiques pour créer un plan personnalisé.
                </p>
            </div>

            {/* Info Card */}
            <div className="bg-zinc-900 rounded-xl p-6 mb-6">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <Sparkles className="text-emerald-500" size={20} />
                    Comment ça marche ?
                </h3>
                <ul className="space-y-2 text-zinc-300 text-sm">
                    <li className="flex items-start gap-2">
                        <span className="text-emerald-500">1.</span>
                        <span>
                            <strong>Analyse de vos données</strong> : HRV, sommeil, fatigue
                            des 7 derniers jours
                        </span>
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-emerald-500">2.</span>
                        <span>
                            <strong>Consultation des recherches</strong> : Périodisation,
                            VMA, HRV, etc.
                        </span>
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-emerald-500">3.</span>
                        <span>
                            <strong>Génération du plan</strong> : 4 semaines adaptées à votre
                            forme actuelle
                        </span>
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-emerald-500">4.</span>
                        <span>
                            <strong>Citations scientifiques</strong> : Chaque séance est
                            justifiée par les références
                        </span>
                    </li>
                </ul>
            </div>

            {/* Generate Button */}
            <div className="mb-6">
                <button
                    onClick={handleGenerate}
                    disabled={loading || success}
                    className="w-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 disabled:from-zinc-700 disabled:to-zinc-700 disabled:text-zinc-500 text-white font-bold py-4 rounded-xl transition-all flex items-center justify-center gap-3 text-lg"
                >
                    {loading ? (
                        <>
                            <Loader2 className="animate-spin" size={24} />
                            L'IA réfléchit... (30-60 secondes)
                        </>
                    ) : success ? (
                        <>
                            <CheckCircle size={24} />
                            Plan généré ! Redirection...
                        </>
                    ) : (
                        <>
                            <Sparkles size={24} />
                            Générer mon plan d'entraînement
                        </>
                    )}
                </button>
            </div>

            {/* Success Message */}
            {success && (
                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 mb-6">
                    <div className="flex items-start gap-3">
                        <CheckCircle className="text-emerald-400 flex-shrink-0" size={24} />
                        <div>
                            <h4 className="text-emerald-400 font-semibold mb-1">
                                Plan généré avec succès !
                            </h4>
                            <p className="text-emerald-200/80 text-sm">
                                Votre plan personnalisé de 4 semaines est prêt. Vous allez être
                                redirigé vers votre programme.
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Error Message */}
            {error && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-6">
                    <div className="flex items-start gap-3">
                        <XCircle className="text-red-400 flex-shrink-0" size={24} />
                        <div>
                            <h4 className="text-red-400 font-semibold mb-1">
                                Erreur lors de la génération
                            </h4>
                            <p className="text-red-200/80 text-sm">{error}</p>
                            <button
                                onClick={() => setError(null)}
                                className="text-red-400 underline text-sm mt-2"
                            >
                                Réessayer
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Prerequisites */}
            <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4">
                <h4 className="text-amber-400 font-semibold mb-2 text-sm">
                    📋 Prérequis
                </h4>
                <ul className="text-amber-200/80 text-sm space-y-1">
                    <li>✓ Profil utilisateur rempli (objectif, niveau, etc.)</li>
                    <li>✓ Au moins 3 jours de métriques synchronisées (HRV, sommeil)</li>
                    <li>✓ Clé API Gemini configurée</li>
                </ul>
            </div>

            {/* Footer */}
            <div className="mt-8 text-center">
                <button
                    onClick={() => router.push("/program")}
                    className="text-zinc-400 hover:text-white transition-colors text-sm"
                >
                    ← Retour au programme
                </button>
            </div>
        </div>
    );
}
