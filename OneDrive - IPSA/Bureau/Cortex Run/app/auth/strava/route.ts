import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/utils/supabase/server'
import { getStravaAuthUrl } from '@/utils/strava/config'
import { redirect } from 'next/navigation'

export async function GET(request: NextRequest) {
    const supabase = await createClient()

    // Check authentication
    const { data: { user } } = await supabase.auth.getUser()

    if (!user) {
        return NextResponse.redirect(new URL('/login', request.url))
    }

    // Generate state token for CSRF protection (use user ID)
    const state = Buffer.from(JSON.stringify({ userId: user.id })).toString('base64')

    // Redirect to Strava OAuth
    const authUrl = getStravaAuthUrl(state)

    return NextResponse.redirect(authUrl)
}
