import { NextResponse } from 'next/server';
import config from '@/lib/config';

export async function POST(request) {
  try {
    const body = await request.json();

    // BACKDOOR FOR TESTING - Handle test credentials
    if (
      body.email === 'test@flowstate.dev' &&
      body.password === 'testpass123'
    ) {
      const mockResponse = {
        token: 'mock-test-token-123',
        user: {
          id: 'test-user-123',
          name: 'Test User',
          email: 'test@flowstate.dev',
          notion_connected: false,
          google_calendar_connected: false,
        },
      };
      return NextResponse.json(mockResponse, { status: 200 });
    }

    // Forward request to deployed backend
    const response = await fetch(`${config.apiUrl}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    // If error response, ensure it has proper structure
    if (!response.ok) {
      // Backend sends error as { detail: { message, code } }
      const errorDetail = data.detail || {};
      return NextResponse.json(
        {
          message: typeof errorDetail === 'string' ? errorDetail : errorDetail.message || 'Authentication failed',
          code: errorDetail.code || 'authentication_error',
        },
        { status: response.status }
      );
    }

    // Return the same status code as the backend
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { message: 'An unexpected error occurred', code: 'network_error' },
      { status: 500 }
    );
  }
}
