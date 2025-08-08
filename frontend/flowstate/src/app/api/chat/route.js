import { NextResponse } from 'next/server';
import config from '@/lib/config';

export async function POST(request) {
  try {
    const body = await request.json();
    console.log('Chat request body:', body);
    
    // Get token from request
    const authHeader = request.headers.get('authorization');
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }
    
    const token = authHeader.split(' ')[1];
    console.log('Token found:', token ? 'Yes' : 'No');
    
    // Forward request to deployed backend
    console.log('Sending request to:', `${config.apiUrl}/api/chat`);
    const response = await fetch(`${config.apiUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(body),
    });
    
    console.log('Backend response status:', response.status);
    console.log('Backend response headers:', Object.fromEntries(response.headers.entries()));
    
    // Get the response text first to see what we're actually getting
    const responseText = await response.text();
    console.log('Backend response text:', responseText);
    
    // Try to parse as JSON
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (parseError) {
      console.error('Failed to parse response as JSON:', parseError);
      return NextResponse.json(
        { error: 'Backend returned invalid response', details: responseText.substring(0, 200) }, 
        { status: 500 }
      );
    }
    
    // Return the same status code as the backend
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Chat API route error:', error);
    return NextResponse.json(
      { error: 'An unexpected error occurred', details: error.message }, 
      { status: 500 }
    );
  }
}