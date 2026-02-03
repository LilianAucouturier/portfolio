// Strava OAuth2 Configuration
export const STRAVA_CONFIG = {
    clientId: process.env.STRAVA_CLIENT_ID!,
    clientSecret: process.env.STRAVA_CLIENT_SECRET!,

    // OAuth endpoints
    authorizationUrl: 'https://www.strava.com/oauth/authorize',
    tokenUrl: 'https://www.strava.com/oauth/token',

    // API endpoint
    apiUrl: 'https://www.strava.com/api/v3',

    // Scopes required
    scopes: ['read', 'activity:read_all'],

    // Redirect URI (must match Strava app settings)
    redirectUri: process.env.NEXT_PUBLIC_BASE_URL
        ? `${process.env.NEXT_PUBLIC_BASE_URL}/auth/strava/callback`
        : 'http://localhost:3000/auth/strava/callback',
}

export function getStravaAuthUrl(state: string): string {
    const params = new URLSearchParams({
        client_id: STRAVA_CONFIG.clientId,
        redirect_uri: STRAVA_CONFIG.redirectUri,
        response_type: 'code',
        scope: STRAVA_CONFIG.scopes.join(','),
        state, // CSRF protection
    })

    return `${STRAVA_CONFIG.authorizationUrl}?${params.toString()}`
}

export interface StravaTokenResponse {
    token_type: 'Bearer'
    expires_at: number
    expires_in: number
    refresh_token: string
    access_token: string
    athlete: {
        id: number
        username: string
        firstname: string
        lastname: string
        profile: string
    }
}

export interface StravaActivity {
    id: number
    name: string
    distance: number // meters
    moving_time: number // seconds
    elapsed_time: number // seconds
    total_elevation_gain: number // meters
    type: string // "Run", "Ride", etc.
    start_date: string // ISO 8601
    average_heartrate?: number
    max_heartrate?: number
    average_speed?: number // meters/second
    max_speed?: number
}
