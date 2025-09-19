import { NextResponse } from 'next/server';
import config from '@/lib/config';

export async function POST(request) {
  try {
    const body = await request.json();
    console.log('Stream request body:', body);

    // Get token from request
    const authHeader = request.headers.get('authorization');
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      );
    }

    const token = authHeader.split(' ')[1];
    console.log('Token found for streaming:', token ? 'Yes' : 'No');

    // Forward streaming request to deployed backend
    console.log(
      'Sending streaming request to:',
      `${config.apiUrl}/api/chat/stream`
    );
    const response = await fetch(`${config.apiUrl}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });

    console.log('Backend streaming response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend streaming error:', errorText);
      return NextResponse.json(
        {
          error: 'Backend streaming failed',
          details: errorText.substring(0, 200),
        },
        { status: response.status }
      );
    }

    // Check if response body exists
    if (!response.body) {
      console.error('No response body for streaming');
      return NextResponse.json(
        { error: 'No streaming data available' },
        { status: 500 }
      );
    }

    // Create a streaming response
    const stream = new ReadableStream({
      async start(controller) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        try {
          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              controller.close();
              break;
            }

            // Decode and forward the chunk
            const chunk = decoder.decode(value, { stream: true });
            controller.enqueue(new TextEncoder().encode(chunk));
          }
        } catch (error) {
          console.error('Streaming error:', error);
          controller.error(error);
        } finally {
          reader.releaseLock();
        }
      },
    });

    // Return streaming response with appropriate headers
    return new NextResponse(stream, {
      headers: {
        'Content-Type': 'text/plain',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });
  } catch (error) {
    console.error('Streaming API error:', error);
    return NextResponse.json(
      { error: 'Streaming request failed', details: error.message },
      { status: 500 }
    );
  }
}
