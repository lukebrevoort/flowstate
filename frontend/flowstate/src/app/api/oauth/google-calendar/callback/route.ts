// Google Calendar OAuth callback API route
import { NextRequest, NextResponse } from 'next/server';
import config from '@/lib/config';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');

    // Handle OAuth error
    if (error) {
      const errorDescription =
        searchParams.get('error_description') || 'OAuth authorization failed';
      return NextResponse.redirect(
        new URL(
          `/OAuth?error=${encodeURIComponent(errorDescription)}`,
          request.url
        )
      );
    }

    // Validate required parameters
    if (!code || !state) {
      return NextResponse.redirect(
        new URL('/OAuth?error=Missing code or state parameter', request.url)
      );
    }

    // Forward the callback to the backend
    const response = await fetch(
      `${config.apiUrl}/api/oauth/google-calendar/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(
        `Backend responded with ${response.status}: ${errorData}`
      );
    }

    const data = await response.json();

    if (data.success) {
      // Redirect to OAuth page with success message
      return NextResponse.redirect(
        new URL(
          `/OAuth?success=Google Calendar connected successfully&email=${encodeURIComponent(data.user_email || 'Unknown')}`,
          request.url
        )
      );
    } else {
      throw new Error(data.message || 'OAuth callback failed');
    }
  } catch (error) {
    console.error('Google Calendar OAuth callback error:', error);
    return NextResponse.redirect(
      new URL(
        `/OAuth?error=${encodeURIComponent('Failed to complete Google Calendar authorization')}`,
        request.url
      )
    );
  }
}
