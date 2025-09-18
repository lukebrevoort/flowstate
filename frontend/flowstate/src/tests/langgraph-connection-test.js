// Simple test script to verify connectivity with the LangGraph backend
import dotenv from 'dotenv';
dotenv.config();

const testLangGraphConnection = async () => {
  console.log('Starting LangGraph connection test...');
  const baseUrl =
    process.env.NEXT_PUBLIC_LANGGRAPH_API_URL || 'http://localhost:9876';
  console.log(`Using API URL: ${baseUrl}`);

  try {
    // 1. Test basic connectivity by listing assistants
    console.log('1. Testing basic connectivity by listing assistants...');
    const assistantResponse = await fetch(`${baseUrl}/assistants`);
    if (!assistantResponse.ok) {
      throw new Error(
        `Failed to list assistants: ${assistantResponse.status} ${assistantResponse.statusText}`
      );
    }
    const assistants = await assistantResponse.json();
    console.log(`✅ Successfully connected to LangGraph API`);
    console.log(`✅ Retrieved ${assistants.length} assistants`);

    if (assistants.length > 0) {
      console.log(`First assistant ID: ${assistants[0].id}`);
    } else {
      console.warn('⚠️ No assistants found in your LangGraph deployment');
    }

    // 2. Test thread creation
    console.log('2. Testing thread creation...');
    const threadResponse = await fetch(`${baseUrl}/threads`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!threadResponse.ok) {
      throw new Error(
        `Failed to create thread: ${threadResponse.status} ${threadResponse.statusText}`
      );
    }
    const thread = await threadResponse.json();
    const threadId = thread.thread_id;
    console.log(`✅ Successfully created thread with ID: ${threadId}`);

    // 3. Test sending a message if assistants are available
    if (assistants.length > 0 && threadId) {
      const assistantId = assistants[0].id;
      console.log(
        `3. Testing message sending with assistant ${assistantId} and thread ${threadId}...`
      );

      const runResponse = await fetch(`${baseUrl}/threads/${threadId}/runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          assistant_id: assistantId,
          input: {
            messages: [
              { role: 'user', content: 'Hello, this is a test message.' },
            ],
          },
        }),
      });

      if (!runResponse.ok) {
        throw new Error(
          `Failed to create run: ${runResponse.status} ${runResponse.statusText}`
        );
      }
      const runResult = await runResponse.json();
      console.log(`✅ Successfully created run with ID: ${runResult.run_id}`);

      // 4. Test getting thread history
      console.log('4. Testing thread history...');
      const historyResponse = await fetch(
        `${baseUrl}/threads/${threadId}/messages`
      );
      if (!historyResponse.ok) {
        throw new Error(
          `Failed to get thread history: ${historyResponse.status} ${historyResponse.statusText}`
        );
      }
      const history = await historyResponse.json();
      console.log(
        `✅ Successfully retrieved thread history with ${history.length} messages`
      );
    }

    console.log(
      'All tests passed! Your LangGraph connection is working correctly.'
    );
    return true;
  } catch (error) {
    console.error('Test failed:', error);
    console.error(
      'This could indicate that your LangGraph Docker API is not running or is not accessible at the URL:',
      baseUrl
    );
    console.log(
      'Make sure your Docker containers are running with: docker-compose up -d'
    );
    console.log(
      'Check if your LangGraph API is using a different endpoint structure.'
    );
    return false;
  }
};

// Run the test
testLangGraphConnection().then(success => {
  console.log(`Test ${success ? 'completed successfully' : 'failed'}`);
});

// Export for use in other files
export default testLangGraphConnection;
