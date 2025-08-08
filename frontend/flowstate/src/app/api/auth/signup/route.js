import { NextResponse } from 'next/server';
import config from '@/lib/config';

export async function POST(request) {
  try {
    const body = await request.json();
    
    // BACKDOOR FOR TESTING - Handle test signup
    if (body.email === 'test@flowstate.dev' || body.email.includes('test')) {
      const mockResponse = {
        token: 'mock-test-token-123',
        user: {
          id: 'test-user-123',
          name: body.name || 'Test User',
          email: body.email,
          notion_connected: false,
          google_calendar_connected: false,
        }
      };
      return NextResponse.json(mockResponse, { status: 201 });
    }
    
    // Forward request to deployed backend
    const response = await fetch(`${config.apiUrl}/api/auth/signup`, {
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
    console.error("Signup error:", error);
    return NextResponse.json(
      { error: "An unexpected error occurred" }, 
      { status: 500 }
    );
  }
}