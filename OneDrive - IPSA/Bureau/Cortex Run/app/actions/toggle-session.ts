"use server";

import { createClient } from "@/utils/supabase/server";
import { revalidatePath } from "next/cache";

export async function toggleSessionCompletion(sessionId: string) {
    const supabase = await createClient();

    try {
        // Get current session
        const { data: session, error: fetchError } = await supabase
            .from("training_sessions")
            .select("completed_at")
            .eq("id", sessionId)
            .single();

        if (fetchError) {
            throw new Error("Session non trouvée");
        }

        // Toggle completion
        const newCompletedAt = session.completed_at ? null : new Date().toISOString();

        const { error: updateError } = await supabase
            .from("training_sessions")
            .update({ completed_at: newCompletedAt })
            .eq("id", sessionId);

        if (updateError) {
            throw new Error("Erreur lors de la mise à jour");
        }

        // Revalidate the program page to show updated state
        revalidatePath("/program");

        return {
            success: true,
            completed: !!newCompletedAt,
        };
    } catch (error: any) {
        return {
            success: false,
            error: error.message,
        };
    }
}
