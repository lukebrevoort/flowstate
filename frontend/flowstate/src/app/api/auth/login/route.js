import { NextResponse } from 'next/server';
import config from '@/lib/config';

export async function POST(request) {
  try {
    const body = await request.json();
    
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