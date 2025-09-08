// Notion OAuth callback API route
import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');

    // Handle OAuth error
    if (error) {
      const errorDescription = searchParams.get('error_description') || 'OAuth authorization failed';
      return NextResponse.redirect(
        new URL(`/OAuth?error=${encodeURIComponent(errorDescription)}`, request.url)
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
      `${BACKEND_URL}/api/oauth/notion/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`Backend responded with ${response.status}: ${errorData}`);
    }

    const data = await response.json();

    if (data.success) {
      // Redirect to OAuth page with success message
      return NextResponse.redirect(
        new URL(`/OAuth?success=Notion connected successfully&workspace=${encodeURIComponent(data.workspace_name || 'Unknown')}`, request.url)
      );
    } else {
      throw new Error(data.message || 'OAuth callback failed');
    }

  } catch (error) {
    console.error('Notion OAuth callback error:', error);
    return NextResponse.redirect(
      new URL(`/OAuth?error=${encodeURIComponent('Failed to complete Notion authorization')}`, request.url)
    );
  }
}
