import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const response = await fetch('http://localhost:5001/api/test');
    const data = await response.json();
    console.log('Data fetched from backend:', data); // Debugging
    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error('Error fetching data:', error); // Debugging
    return NextResponse.json(
      { error: 'Failed to fetch data' },
      { status: 500 }
    );
  }
}
