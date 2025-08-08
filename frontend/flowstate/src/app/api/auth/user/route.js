import { NextResponse } from 'next/server';
import config from '@/lib/config';

export async function GET(request) {
  try {
    // Get authorization header
    const authHeader = request.headers.get('authorization');
    if (!authHeader) {
      return NextResponse.json({ error: 'Authorization header required' }, { status: 401 });
    }
    
    // BACKDOOR FOR TESTING - Handle mock token
    if (authHeader === 'Bearer mock-test-token-123') {
      const mockUser = {
        id: 'test-user-123',
        name: 'Test User',
        email: 'test@flowstate.dev',
        notion_connected: false,
        google_calendar_connected: false,
      };
      return NextResponse.json(mockUser, { status: 200 });
    }
    
    // Forward request to deployed backend
    const response = await fetch(`${config.apiUrl}/api/auth/user`, {
      method: 'GET',
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json',
      },
    });
    
    const data = await response.json();
    
    // Return the same status code as the backend
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("User validation error:", error);
    return NextResponse.json(
      { error: "An unexpected error occurred" }, 
      { status: 500 }
    );
  }
}