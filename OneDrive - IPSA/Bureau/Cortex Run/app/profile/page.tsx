import { createClient } from "@/utils/supabase/server";
import { redirect } from "next/navigation";
import ProfilePageClient from "@/components/ProfilePageClient";

export default async function ProfilePage() {
    const supabase = await createClient();

    // Check authentication
    const {
        data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
        redirect("/login");
    }

    // Fetch user profile with Strava connection info
    const { data: userProfile } = await supabase
        .from("users")
        .select("strava_access_token, strava_last_sync_at")
        .eq("id", user.id)
        .single();

    const stravaConnected = !!userProfile?.strava_access_token;
    const stravaLastSync = userProfile?.strava_last_sync_at || null;

    return (
        <ProfilePageClient
            user={user}
            stravaConnected={stravaConnected}
            stravaLastSync={stravaLastSync}
        />
    );
}
