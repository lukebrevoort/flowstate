import { NextResponse } from 'next/server';
import config from '@/lib/config';

export async function POST(request) {
  try {
    const body = await request.json();
    
    // BACKDOOR FOR TESTING - Handle test credentials
    if (body.email === 'test@flowstate.dev' && body.password === 'testpass123') {
      const mockResponse = {
        token: 'mock-test-token-123',
        user: {
          id: 'test-user-123',
          name: 'Test User',
          email: 'test@flowstate.dev',
          notion_connected: false,
          google_calendar_connected: false,
        }
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
    
    // Return the same status code as the backend
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Login error:", error);
    return NextResponse.json(
      { error: "An unexpected error occurred" }, 
      { status: 500 }
    );
  }
}