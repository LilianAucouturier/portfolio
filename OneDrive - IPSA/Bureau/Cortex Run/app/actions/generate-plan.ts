"use server";

import { createClient } from "@/utils/supabase/server";
import { generateContent } from "@/utils/ai/gemini";
import { redirect } from "next/navigation";

interface TrainingPlan {
    analysis: string;
    philosophy: string;
    weeks: Array<{
        week_number: number;
        theme: string;
        total_volume_km: number;
        sessions: Array<{
            day: string;
            type: string;
            distance_km: number | null;
            duration_minutes: number | null;
            pace_range: string | null;
            hr_zone: number | null;
            rationale: string;
            workout_structure: any;
        }>;
    }>;
    key_principles_applied: string[];
    sources_used: string[];
}

export async function generateTrainingPlan(userId: string) {
    const supabase = await createClient();

    try {
        // ============================================
        // STEP A: Récupérer le profil utilisateur
        // ============================================
        const { data: userProfile, error: userError } = await supabase
            .from("users")
            .select("*")
            .eq("id", userId)
            .single();

        if (userError || !userProfile) {
            throw new Error("Impossible de récupérer le profil utilisateur");
        }

        // ============================================
        // STEP B: Récupérer métriques santé (7 derniers jours)
        // ============================================
        const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
            .toISOString()
            .split("T")[0];

        const { data: metrics, error: metricsError } = await supabase
            .from("daily_metrics")
            .select("*")
            .eq("user_id", userId)
            .gte("date", sevenDaysAgo)
            .order("date", { ascending: false });

        // Calculer les moyennes
        const avgHRV =
            metrics && metrics.length > 0
                ? Math.round(
                    metrics.reduce((sum, m) => sum + (m.hrv_ms || 0), 0) /
                    metrics.length
                )
                : null;

        const avgSleep =
            metrics && metrics.length > 0
                ? (
                    metrics.reduce(
                        (sum, m) => sum + (m.sleep_duration_hours || 0),
                        0
                    ) / metrics.length
                ).toFixed(1)
                : null;

        const avgFatigue =
            metrics && metrics.length > 0
                ? (
                    metrics.reduce((sum, m) => sum + (m.fatigue_score || 5), 0) /
                    metrics.length
                ).toFixed(1)
                : null;

        const avgRestingHR =
            metrics && metrics.length > 0
                ? Math.round(
                    metrics.reduce((sum, m) => sum + (m.resting_hr || 0), 0) /
                    metrics.length
                )
                : null;

        // Tendance HRV (compare derniers 3 jours vs 7 jours)
        const recentHRV =
            metrics && metrics.length >= 3
                ? Math.round(
                    metrics
                        .slice(0, 3)
                        .reduce((sum, m) => sum + (m.hrv_ms || 0), 0) / 3
                )
                : avgHRV;

        const hrvTrend = recentHRV && avgHRV ? recentHRV - avgHRV : 0;

        // ============================================
        // STEP C: Récupérer les documents scientifiques
        // ============================================
        const { data: knowledgeDocs, error: docsError } = await supabase
            .from("knowledge_docs")
            .select("title, content, topics")
            .order("created_at", { ascending: true });

        if (docsError) {
            throw new Error("Erreur lors de la récupération des documents");
        }

        // Filtrer les docs pertinents selon l'objectif
        const relevantDocs = knowledgeDocs?.filter((doc) => {
            const goalType = userProfile.goal_type || "10k";
            return (
                doc.topics.includes(goalType) ||
                doc.topics.includes("periodization") ||
                doc.topics.includes("recovery") ||
                doc.topics.includes(userProfile.experience_level || "intermediate")
            );
        });

        // ============================================
        // STEP D: Construire le prompt Gemini
        // ============================================
        const knowledgeContext = (relevantDocs || knowledgeDocs || [])
            .map((doc) => {
                return `### ${doc.title}\n\n${doc.content.substring(0, 4000)}\n---\n`;
            })
            .join("\n\n");

        const prompt = `# RÔLE
Tu es un coach running IA expert en périodisation, physiologie de l'effort et sciences de l'entraînement.

Tu combines OBLIGATOIREMENT :
1. Les principes scientifiques fournis dans les RÉFÉRENCES ci-dessous
2. Tes connaissances propres en coaching sportif
3. Les données individuelles de l'athlète (CONTEXTE)

# RÉFÉRENCES SCIENTIFIQUES (À SUIVRE SCRUPULEUSEMENT)

${knowledgeContext}

# CONTEXTE ATHLÈTE

**Profil** :
- Nom : ${userProfile.name || "Athlète"}
- Niveau : ${userProfile.experience_level || "intermédiaire"}
- Objectif : ${userProfile.goal_type || "10k"} le ${userProfile.goal_date ? new Date(userProfile.goal_date).toLocaleDateString("fr-FR") : "Date non définie"}
- Volume actuel : ${userProfile.current_weekly_volume_km || "Non renseigné"} km/semaine
- FC Max : ${userProfile.max_hr || "Non renseigné"} bpm
- FC Repos : ${userProfile.rest_hr || avgRestingHR || "Non renseigné"} bpm

**Données récentes (7 derniers jours)** :
- HRV moyenne : ${avgHRV || "Non disponible"} ms
- Tendance HRV : ${hrvTrend > 0 ? `+${hrvTrend}ms (en hausse ✅)` : hrvTrend < 0 ? `${hrvTrend}ms (en baisse ⚠️)` : "stable"}
- Sommeil moyen : ${avgSleep || "Non disponible"}h/nuit
- Fatigue subjective : ${avgFatigue || "Non renseigné"}/10
- FC Repos moyenne : ${avgRestingHR || "Non disponible"} bpm

**Interprétation Récupération** :
${avgHRV && avgHRV < 50 ? "⚠️ HRV BASSE → Priorité récupération, éviter intensité élevée cette semaine" : ""}
${avgSleep && parseFloat(avgSleep) < 7 ? "⚠️ SOMMEIL INSUFFISANT → Réduire volume ou intensité" : ""}
${avgFatigue && parseFloat(avgFatigue) < 5 ? "⚠️ FATIGUE ÉLEVÉE → Semaine allégée recommandée" : ""}

# CONTRAINTES IMPÉRATIVES

1. **Périodisation** : Applique les principes de périodisation décrits dans les références (Base → Développement → Affûtage)
2. **Progressivité** : Respecte la RÈGLE DES 10% (volume hebdomadaire ne doit pas augmenter de +10%)
3. **Récupération** : Intègre OBLIGATOIREMENT 1-2 jours de repos complet/semaine
4. **Adaptation HRV** : Si HRV en baisse >10% → semaine de récupération forcée
5. **Zones d'effort** : Utilise les 5 zones FC (Z1=récup, Z2=endurance, Z3=tempo, Z4=seuil, Z5=VMA)
6. **Citations** : CITE systématiquement tes sources (Référence PDF ou "Connaissances IA")

# DURÉE DU PLAN

Génère un plan de **4 semaines** (1 mois) avec progression adaptée.

# INSTRUCTIONS DE GÉNÉRATION

1. **Analyse** : Résume l'état actuel de l'athlète (récupération, volume, objectif)
2. **Philosophie** : Explique l'approche globale du plan (ex: "Periodisation polarisée sur 4 semaines")
3. **Semaines** : Pour chaque semaine :
   - Définis un **thème** (ex: "Base endurance", "Développement seuil", "Récupération")
   - Calcule le **volume total** (km)
   - Prescris **4-6 séances/semaine** avec :
     * Type de séance (endurance, tempo, intervals, long_run, recovery, rest)
     * Distance OU Durée (au moins un des deux)
     * Plage d'allure (ex: "5:30-6:00 /km")
     * Zone FC cible (1-5)
     * **Rationale** : Pourquoi cette séance ? (cite la source)
     * Structure détaillée (échauffement, corps, retour calme)

4. **Principes appliqués** : Liste les principes scientifiques utilisés
5. **Sources** : Liste TOUTES les sources consultées

# FORMAT DE SORTIE (JSON STRICT)

Réponds UNIQUEMENT avec du JSON valide (pas de markdown, pas de texte avant/après).

\`\`\`json
{
  "analysis": "Analyse de l'état actuel (2-3 phrases)",
  "philosophy": "Approche globale (1 phrase)",
  "weeks": [
    {
      "week_number": 1,
      "theme": "Base endurance",
      "total_volume_km": 30,
      "sessions": [
        {
          "day": "Lundi",
          "type": "rest",
          "distance_km": null,
          "duration_minutes": null,
          "pace_range": null,
          "hr_zone": null,
          "rationale": "Récupération post-weekend",
          "workout_structure": null
        },
        {
          "day": "Mardi",
          "type": "endurance",
          "distance_km": 8,
          "duration_minutes": 50,
          "pace_range": "6:00-6:30 /km",
          "hr_zone": 2,
          "rationale": "Course facile Z2 pour développer base aérobie (Réf: Lydiard Running to the Top)",
          "workout_structure": {
            "warmup": "5min marche",
            "main": "40min Z2",
            "cooldown": "5min marche"
          }
        }
      ]
    }
  ],
  "key_principles_applied": [
    "Periodization (Lydiard)",
    "HRV-guided intensity",
    "Progressive overload (10% rule)"
  ],
  "sources_used": [
    "PDF: Principes de Périodisation pour le 10km",
    "AI Knowledge: VO2max adaptation timeline"
  ]
}
\`\`\`

# GÉNÈRE LE PLAN MAINTENANT

Respecte SCRUPULEUSEMENT les références scientifiques. Ne génère RIEN qui contredise les documents fournis.
`;

        // ============================================
        // STEP E: Appeler Gemini et parser la réponse
        // ============================================
        console.log("🤖 Appel Gemini API...");
        const rawResponse = await generateContent(prompt);

        // Nettoyer la réponse (enlever markdown si présent)
        let jsonResponse = rawResponse.trim();
        if (jsonResponse.startsWith("```json")) {
            jsonResponse = jsonResponse.replace(/```json\n?/g, "").replace(/```\n?/g, "");
        } else if (jsonResponse.startsWith("```")) {
            jsonResponse = jsonResponse.replace(/```\n?/g, "");
        }

        const parsedPlan: TrainingPlan = JSON.parse(jsonResponse);

        console.log("✅ Plan généré:", parsedPlan.philosophy);

        // ============================================
        // STEP F: Insérer dans training_plans
        // ============================================
        const { data: newPlan, error: planError } = await supabase
            .from("training_plans")
            .insert({
                user_id: userId,
                start_date: new Date().toISOString().split("T")[0],
                status: "active",
                coaching_philosophy: parsedPlan.philosophy,
                total_weeks: parsedPlan.weeks.length,
                generation_context: {
                    avg_hrv_7d: avgHRV,
                    avg_sleep_7d: avgSleep,
                    avg_fatigue_7d: avgFatigue,
                    hrv_trend: hrvTrend,
                    goal_type: userProfile.goal_type,
                    goal_date: userProfile.goal_date,
                },
            })
            .select()
            .single();

        if (planError || !newPlan) {
            throw new Error("Erreur lors de l'insertion du plan : " + planError?.message);
        }

        console.log("📅 Plan créé avec ID:", newPlan.id);

        // ============================================
        // STEP G: Insérer les séances dans training_sessions
        // ============================================
        const allSessions = parsedPlan.weeks.flatMap((week) => {
            return week.sessions.map((session, index) => {
                // Calculer la date de la séance
                const sessionDate = new Date();
                sessionDate.setDate(
                    sessionDate.getDate() + (week.week_number - 1) * 7 + index
                );

                return {
                    plan_id: newPlan.id,
                    date: sessionDate.toISOString().split("T")[0],
                    week_number: week.week_number,
                    session_type: session.type,
                    target_distance_km: session.distance_km,
                    target_duration_minutes: session.duration_minutes,
                    target_pace_range: session.pace_range,
                    target_hr_zone: session.hr_zone,
                    rationale: session.rationale,
                    workout_structure: session.workout_structure,
                };
            });
        });

        const { error: sessionsError } = await supabase
            .from("training_sessions")
            .insert(allSessions);

        if (sessionsError) {
            throw new Error("Erreur lors de l'insertion des séances : " + sessionsError.message);
        }

        console.log(`✅ ${allSessions.length} séances insérées`);

        // ============================================
        // STEP H: Logger la génération dans ai_generations
        // ============================================
        await supabase.from("ai_generations").insert({
            user_id: userId,
            generation_type: "training_plan",
            prompt_template: "Training Plan Generator v1",
            prompt_context: {
                avg_hrv: avgHRV,
                avg_sleep: avgSleep,
                goal: userProfile.goal_type,
                docs_used: relevantDocs?.length || 0,
            },
            raw_response: rawResponse,
            response_status: "success",
            parsed_output: parsedPlan,
        });

        return {
            success: true,
            planId: newPlan.id,
            message: "Plan d'entraînement généré avec succès !",
        };
    } catch (error: any) {
        console.error("❌ Erreur génération plan:", error);

        // Logger l'erreur
        await supabase.from("ai_generations").insert({
            user_id: userId,
            generation_type: "training_plan",
            response_status: "error",
            error_message: error.message,
        });

        return {
            success: false,
            error: error.message || "Erreur inconnue",
        };
    }
}
