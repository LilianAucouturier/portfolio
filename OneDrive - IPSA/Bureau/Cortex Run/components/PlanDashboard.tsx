"use client";

import { useState } from "react";
import SessionCard from "./SessionCard";
import { ChevronLeft, ChevronRight, Calendar } from "lucide-react";

interface Session {
    id: string;
    date: string;
    week_number: number;
    session_type: string;
    target_distance_km: number | null;
    target_duration_minutes: number | null;
    target_pace_range: string | null;
    target_hr_zone: number | null;
    rationale: string | null;
    completed_at: string | null;
    workout_structure: any;
}

interface Plan {
    id: string;
    coaching_philosophy: string | null;
    total_weeks: number;
    start_date: string;
}

interface PlanDashboardProps {
    plan: Plan;
    sessions: Session[];
}

const DAY_NAMES = [
    "Lundi",
    "Mardi",
    "Mercredi",
    "Jeudi",
    "Vendredi",
    "Samedi",
    "Dimanche",
];

export default function PlanDashboard({ plan, sessions }: PlanDashboardProps) {
    // Determine current week based on start_date and today
    const startDate = new Date(plan.start_date);
    const today = new Date();
    const daysSinceStart = Math.floor(
        (today.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)
    );
    const initialWeek = Math.max(1, Math.min(Math.ceil((daysSinceStart + 1) / 7), plan.total_weeks));

    const [selectedWeek, setSelectedWeek] = useState(initialWeek);

    // Filter sessions for selected week
    const weekSessions = sessions.filter((s) => s.week_number === selectedWeek);

    // Group sessions by day name (sessions should already have dates)
    const sessionsByDay: { [key: string]: Session } = {};
    weekSessions.forEach((session) => {
        const sessionDate = new Date(session.date);
        const dayIndex = (sessionDate.getDay() + 6) % 7; // Convert Sunday=0 to Lundi=0
        const dayName = DAY_NAMES[dayIndex];
        sessionsByDay[dayName] = session;
    });

    // Calculate week stats
    const completedCount = weekSessions.filter((s) => s.completed_at).length;
    const totalSessions = weekSessions.length;
    const completionRate =
        totalSessions > 0 ? Math.round((completedCount / totalSessions) * 100) : 0;

    const totalDistance = weekSessions.reduce(
        (sum, s) => sum + (s.target_distance_km || 0),
        0
    );
    const completedDistance = weekSessions
        .filter((s) => s.completed_at)
        .reduce((sum, s) => sum + (s.target_distance_km || 0), 0);

    return (
        <div>
            {/* Plan Philosophy */}
            {plan.coaching_philosophy && (
                <div className="bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border border-emerald-500/20 rounded-xl p-4 mb-6">
                    <p className="text-sm text-emerald-300/80 mb-1 font-medium flex items-center gap-2">
                        <span>🧠</span>
                        <span>Philosophie du plan</span>
                    </p>
                    <p className="text-white text-sm leading-relaxed">
                        {plan.coaching_philosophy}
                    </p>
                </div>
            )}

            {/* Week Selector */}
            <div className="flex items-center justify-between mb-6">
                <button
                    onClick={() => setSelectedWeek(Math.max(1, selectedWeek - 1))}
                    disabled={selectedWeek === 1}
                    className="p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                    <ChevronLeft size={20} />
                </button>

                <div className="flex items-center gap-3">
                    <Calendar size={20} className="text-emerald-500" />
                    <div className="text-center">
                        <h2 className="text-2xl font-bold">Semaine {selectedWeek}</h2>
                        <p className="text-sm text-zinc-400">
                            {selectedWeek === initialWeek ? "En cours" : ""}
                        </p>
                    </div>
                </div>

                <button
                    onClick={() =>
                        setSelectedWeek(Math.min(plan.total_weeks, selectedWeek + 1))
                    }
                    disabled={selectedWeek === plan.total_weeks}
                    className="p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                    <ChevronRight size={20} />
                </button>
            </div>

            {/* Week Stats */}
            <div className="grid grid-cols-3 gap-3 mb-6">
                <div className="bg-zinc-900 rounded-xl p-3">
                    <p className="text-xs text-zinc-500 mb-1">Séances</p>
                    <p className="text-lg font-bold">
                        {completedCount}/{totalSessions}
                    </p>
                    <p className="text-xs text-emerald-500">{completionRate}%</p>
                </div>

                <div className="bg-zinc-900 rounded-xl p-3">
                    <p className="text-xs text-zinc-500 mb-1">Distance</p>
                    <p className="text-lg font-bold">{totalDistance.toFixed(0)} km</p>
                    <p className="text-xs text-emerald-500">
                        {completedDistance.toFixed(0)} km fait
                    </p>
                </div>

                <div className="bg-zinc-900 rounded-xl p-3">
                    <p className="text-xs text-zinc-500 mb-1">Semaine</p>
                    <p className="text-lg font-bold">
                        {selectedWeek}/{plan.total_weeks}
                    </p>
                    <p className="text-xs text-zinc-400">
                        {plan.total_weeks - selectedWeek} restantes
                    </p>
                </div>
            </div>

            {/* Sessions Grid */}
            <div className="space-y-3">
                {DAY_NAMES.map((dayName) => {
                    const session = sessionsByDay[dayName];
                    if (session) {
                        return (
                            <SessionCard
                                key={session.id}
                                session={session}
                                dayName={dayName}
                            />
                        );
                    }
                    return null;
                })}

                {weekSessions.length === 0 && (
                    <div className="bg-zinc-900 rounded-xl p-6 text-center">
                        <p className="text-zinc-500">Aucune séance pour cette semaine</p>
                    </div>
                )}
            </div>
        </div>
    );
}
