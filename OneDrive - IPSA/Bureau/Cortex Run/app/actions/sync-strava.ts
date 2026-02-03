"use server";

import { createClient } from "@/utils/supabase/server";
import { STRAVA_CONFIG, type StravaActivity, type StravaTokenResponse } from "@/utils/strava/config";
import { revalidatePath } from "next/cache";

/**
 * Refresh Strava access token if expired
 */
async function refreshStravaToken(
    userId: string,
    refreshToken: string
): Promise<{ accessToken: string; expiresAt: string } | null> {
    try {
        const response = await fetch(STRAVA_CONFIG.tokenUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                client_id: STRAVA_CONFIG.clientId,
                client_secret: STRAVA_CONFIG.clientSecret,
                refresh_token: refreshToken,
                grant_type: "refresh_token",
            }),
        });

        if (!response.ok) {
            console.error("Failed to refresh Strava token:", response.statusText);
            return null;
        }

        const tokenData: StravaTokenResponse = await response.json();

        // Update tokens in database
        const supabase = await createClient();
        await supabase
            .from("users")
            .update({
                strava_access_token: tokenData.access_token,
                strava_refresh_token: tokenData.refresh_token,
                strava_token_expires_at: new Date(tokenData.expires_at * 1000).toISOString(),
                updated_at: new Date().toISOString(),
            })
            .eq("id", userId);

        return {
            accessToken: tokenData.access_token,
            expiresAt: new Date(tokenData.expires_at * 1000).toISOString(),
        };
    } catch (error) {
        console.error("Error refreshing Strava token:", error);
        return null;
    }
}

/**
 * Get valid Strava access token (refresh if needed)
 */
async function getValidStravaToken(
    userId: string
): Promise<string | null> {
    const supabase = await createClient();

    const { data: user, error } = await supabase
        .from("users")
        .select("strava_access_token, strava_refresh_token, strava_token_expires_at")
        .eq("id", userId)
        .single();

    if (error || !user) {
        return null;
    }

    if (!user.strava_access_token || !user.strava_refresh_token) {
        return null;
    }

    // Check if token is expired (with 5 min buffer)
    const expiresAt = new Date(user.strava_token_expires_at);
    const now = new Date();
    const buffer = 5 * 60 * 1000; // 5 minutes

    if (expiresAt.getTime() - now.getTime() < buffer) {
        // Token expired or about to expire - refresh it
        console.log("🔄 Refreshing Strava token...");
        const refreshed = await refreshStravaToken(userId, user.strava_refresh_token);

        if (!refreshed) {
            return null;
        }

        return refreshed.accessToken;
    }

    return user.strava_access_token;
}

/**
 * Sync Strava activities to database
 */
export async function syncStravaActivities() {
    const supabase = await createClient();

    try {
        // Get authenticated user
        const {
            data: { user },
        } = await supabase.auth.getUser();

        if (!user) {
            return { success: false, error: "Non authentifié" };
        }

        // Get valid access token (refresh if needed)
        const accessToken = await getValidStravaToken(user.id);

        if (!accessToken) {
            return {
                success: false,
                error: "Token Strava invalide. Veuillez vous reconnecter.",
            };
        }

        // Fetch last 30 activities from Strava
        const activitiesResponse = await fetch(
            `${STRAVA_CONFIG.apiUrl}/athlete/activities?per_page=30`,
            {
                headers: {
                    Authorization: `Bearer ${accessToken}`,
                },
            }
        );

        if (!activitiesResponse.ok) {
            throw new Error("Échec de la récupération des activités Strava");
        }

        const activities: StravaActivity[] = await activitiesResponse.json();

        // Filter only running activities
        const runActivities = activities.filter((a) => a.type === "Run");

        if (runActivities.length === 0) {
            return {
                success: true,
                message: "Aucune nouvelle course à synchroniser",
                count: 0,
            };
        }

        // Insert activities (avoid duplicates with strava_id)
        let insertedCount = 0;
        let skippedCount = 0;

        for (const activity of runActivities) {
            // Check if activity already exists
            const { data: existing } = await supabase
                .from("activities")
                .select("id")
                .eq("user_id", user.id)
                .eq("strava_id", activity.id.toString())
                .single();

            if (existing) {
                skippedCount++;
                continue;
            }

            // Insert new activity
            const { error: insertError } = await supabase.from("activities").insert({
                user_id: user.id,
                strava_id: activity.id.toString(),
                activity_date: new Date(activity.start_date).toISOString().split("T")[0],
                activity_type: "run",
                distance_km: (activity.distance / 1000).toFixed(2), // meters → km
                duration_minutes: Math.round(activity.moving_time / 60), // seconds → minutes
                elevation_gain_m: Math.round(activity.total_elevation_gain),
                average_hr: activity.average_heartrate
                    ? Math.round(activity.average_heartrate)
                    : null,
                max_hr: activity.max_heartrate ? Math.round(activity.max_heartrate) : null,
                average_pace_min_per_km: activity.average_speed
                    ? ((1000 / activity.average_speed) / 60).toFixed(2) // m/s → min/km
                    : null,
                notes: activity.name || null,
            });

            if (insertError) {
                console.error("Error inserting activity:", insertError);
            } else {
                insertedCount++;
            }
        }

        // Update last sync timestamp in users table
        await supabase
            .from("users")
            .update({ strava_last_sync_at: new Date().toISOString() })
            .eq("id", user.id);

        // Revalidate profile page
        revalidatePath("/profile");

        return {
            success: true,
            message: `${insertedCount} nouvelle(s) course(s) synchronisée(s)`,
            count: insertedCount,
            skipped: skippedCount,
        };
    } catch (error: any) {
        console.error("❌ Erreur sync Strava:", error);
        return {
            success: false,
            error: error.message || "Erreur inconnue",
        };
    }
}
