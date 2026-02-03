"use client";

import { toggleSessionCompletion } from "@/app/actions/toggle-session";
import {
    CheckCircle2,
    Circle,
    Moon,
    Zap,
    Activity,
    Mountain,
    Heart,
    Wind,
} from "lucide-react";
import { useState } from "react";

interface Session {
    id: string;
    date: string;
    session_type: string;
    target_distance_km: number | null;
    target_duration_minutes: number | null;
    target_pace_range: string | null;
    target_hr_zone: number | null;
    rationale: string | null;
    completed_at: string | null;
    workout_structure: any;
}

interface SessionCardProps {
    session: Session;
    dayName: string;
}

const SESSION_ICONS = {
    rest: Moon,
    recovery: Heart,
    endurance: Activity,
    tempo: Wind,
    intervals: Zap,
    long_run: Mountain,
};

const SESSION_LABELS = {
    rest: "Repos",
    recovery: "Récupération",
    endurance: "Endurance",
    tempo: "Tempo",
    intervals: "Fractionné",
    long_run: "Sortie Longue",
};

export default function SessionCard({ session, dayName }: SessionCardProps) {
    const [isCompleting, setIsCompleting] = useState(false);
    const isCompleted = !!session.completed_at;
    const isRest = session.session_type === "rest";

    const Icon =
        SESSION_ICONS[session.session_type as keyof typeof SESSION_ICONS] ||
        Activity;
    const label =
        SESSION_LABELS[session.session_type as keyof typeof SESSION_LABELS] ||
        session.session_type;

    const handleToggle = async () => {
        setIsCompleting(true);
        await toggleSessionCompletion(session.id);
        setIsCompleting(false);
    };

    // Rest day styling
    if (isRest) {
        return (
            <div className="bg-zinc-900/50 rounded-xl p-4 border border-zinc-800">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                        <Moon size={20} className="text-zinc-500" />
                        <h3 className="font-semibold text-zinc-400">{dayName}</h3>
                    </div>
                </div>
                <p className="text-sm text-zinc-500">Jour de repos</p>
                {session.rationale && (
                    <p className="text-xs text-zinc-600 mt-2 italic">
                        {session.rationale}
                    </p>
                )}
            </div>
        );
    }

    return (
        <div
            className={`rounded-xl p-4 border transition-all ${isCompleted
                    ? "bg-emerald-500/10 border-emerald-500/30"
                    : "bg-zinc-900 border-zinc-800 hover:border-zinc-700"
                }`}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <Icon
                        size={20}
                        className={isCompleted ? "text-emerald-400" : "text-emerald-500"}
                    />
                    <div>
                        <h3
                            className={`font-semibold ${isCompleted ? "text-emerald-400" : "text-white"}`}
                        >
                            {dayName}
                        </h3>
                        <p
                            className={`text-xs ${isCompleted ? "text-emerald-500/70" : "text-zinc-500"}`}
                        >
                            {label}
                        </p>
                    </div>
                </div>

                {/* Completion Toggle */}
                <button
                    onClick={handleToggle}
                    disabled={isCompleting}
                    className="p-1 hover:scale-110 transition-transform disabled:opacity-50"
                >
                    {isCompleted ? (
                        <CheckCircle2 className="text-emerald-500" size={24} />
                    ) : (
                        <Circle className="text-zinc-600 hover:text-zinc-400" size={24} />
                    )}
                </button>
            </div>

            {/* Session Details */}
            <div className="space-y-2 mb-3">
                {session.target_distance_km && (
                    <div className="flex items-center gap-2 text-sm">
                        <span className="text-zinc-500">📍</span>
                        <span className={isCompleted ? "text-emerald-300" : "text-white"}>
                            {session.target_distance_km} km
                        </span>
                    </div>
                )}

                {session.target_duration_minutes && (
                    <div className="flex items-center gap-2 text-sm">
                        <span className="text-zinc-500">⏱️</span>
                        <span className={isCompleted ? "text-emerald-300" : "text-white"}>
                            {session.target_duration_minutes} min
                        </span>
                    </div>
                )}

                {session.target_pace_range && (
                    <div className="flex items-center gap-2 text-sm">
                        <span className="text-zinc-500">🏃</span>
                        <span
                            className={
                                isCompleted ? "text-emerald-300" : "text-zinc-300"
                            }
                        >
                            {session.target_pace_range}
                        </span>
                    </div>
                )}

                {session.target_hr_zone && (
                    <div className="flex items-center gap-2 text-sm">
                        <span className="text-zinc-500">❤️</span>
                        <span
                            className={
                                isCompleted ? "text-emerald-300" : "text-zinc-300"
                            }
                        >
                            Zone {session.target_hr_zone}
                        </span>
                    </div>
                )}
            </div>

            {/* AI Rationale */}
            {session.rationale && (
                <div
                    className={`text-xs p-3 rounded-lg ${isCompleted
                            ? "bg-emerald-500/5 text-emerald-200/80 border border-emerald-500/20"
                            : "bg-zinc-800/50 text-zinc-400 border border-zinc-700/50"
                        }`}
                >
                    <p className="font-medium mb-1 flex items-center gap-1">
                        <span>🧠</span>
                        <span>Pourquoi cette séance ?</span>
                    </p>
                    <p className="leading-relaxed">{session.rationale}</p>
                </div>
            )}

            {/* Completed Date */}
            {isCompleted && session.completed_at && (
                <p className="text-xs text-emerald-500/70 mt-2">
                    ✓ Terminée le{" "}
                    {new Date(session.completed_at).toLocaleDateString("fr-FR")}
                </p>
            )}
        </div>
    );
}
