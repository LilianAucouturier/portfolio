import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/utils/supabase/server'
import { STRAVA_CONFIG, type StravaTokenResponse } from '@/utils/strava/config'

export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams
    const code = searchParams.get('code')
    const state = searchParams.get('state')
    const error = searchParams.get('error')

    // Handle Strava authorization denial
    if (error) {
        return NextResponse.redirect(
            new URL('/profile?strava_error=access_denied', request.url)
        )
    }

    if (!code || !state) {
        return NextResponse.redirect(
            new URL('/profile?strava_error=missing_params', request.url)
        )
    }

    const supabase = await createClient()

    // Verify state token (CSRF protection)
    try {
        const decodedState = JSON.parse(Buffer.from(state, 'base64').toString())
        const { data: { user } } = await supabase.auth.getUser()

        if (!user || decodedState.userId !== user.id) {
            return NextResponse.redirect(
                new URL('/profile?strava_error=invalid_state', request.url)
            )
        }

        // Exchange code for access token
        const tokenResponse = await fetch(STRAVA_CONFIG.tokenUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                client_id: STRAVA_CONFIG.clientId,
                client_secret: STRAVA_CONFIG.clientSecret,
                code,
                grant_type: 'authorization_code',
            }),
        })

        if (!tokenResponse.ok) {
            throw new Error('Failed to exchange code for token')
        }

        const tokenData: StravaTokenResponse = await tokenResponse.json()

        // Store tokens in users table
        const { error: updateError } = await supabase
            .from('users')
            .update({
                strava_access_token: tokenData.access_token,
                strava_refresh_token: tokenData.refresh_token,
                strava_token_expires_at: new Date(tokenData.expires_at * 1000).toISOString(),
                strava_athlete_id: tokenData.athlete.id.toString(),
                updated_at: new Date().toISOString(),
            })
            .eq('id', user.id)

        if (updateError) {
            console.error('Error storing Strava tokens:', updateError)
            return NextResponse.redirect(
                new URL('/profile?strava_error=storage_failed', request.url)
            )
        }

        // Success - redirect to profile with success message
        return NextResponse.redirect(
            new URL('/profile?strava_connected=true', request.url)
        )

    } catch (error) {
        console.error('Strava OAuth callback error:', error)
        return NextResponse.redirect(
            new URL('/profile?strava_error=unknown', request.url)
        )
    }
}
