import testLangGraphConnection from '@/tests/langgraph-connection-test'

// Mock fetch globally
global.fetch = jest.fn()

describe('LangGraph Connection Test', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Reset fetch mock
    ;(global.fetch as jest.Mock).mockClear()
  })

  test('successfully connects to LangGraph API', async () => {
    // Mock successful responses
    ;(global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ id: 'test-assistant-1' }]
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ thread_id: 'test-thread-123' })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: 'test-run-456', status: 'completed' })
      })

    const result = await testLangGraphConnection()
    expect(result).toBe(true)
    
    // Verify the correct API calls were made
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/assistants')
    )
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/threads'),
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
    )
  })

  test('handles API connection failure gracefully', async () => {
    // Mock failed response
    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error'
    })

    const result = await testLangGraphConnection()
    expect(result).toBe(false)
    
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/assistants')
    )
  })

  test('handles network error gracefully', async () => {
    // Mock network error
    ;(global.fetch as jest.Mock).mockRejectedValueOnce(
      new Error('Network error')
    )

    const result = await testLangGraphConnection()
    expect(result).toBe(false)
  })

  test('handles empty assistants list', async () => {
    // Mock successful response with no assistants
    ;(global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => []
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ thread_id: 'test-thread-123' })
      })

    const result = await testLangGraphConnection()
    expect(result).toBe(true)
    
    // Should still try to create a thread even with no assistants
    expect(global.fetch).toHaveBeenCalledTimes(2)
  })

  test('uses correct API URL from environment', async () => {
    const customUrl = 'http://custom-api:9999'
    const originalEnv = process.env.NEXT_PUBLIC_LANGGRAPH_API_URL
    process.env.NEXT_PUBLIC_LANGGRAPH_API_URL = customUrl

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => []
    })

    await testLangGraphConnection()

    expect(global.fetch).toHaveBeenCalledWith(`${customUrl}/assistants`)
    
    // Restore original environment
    process.env.NEXT_PUBLIC_LANGGRAPH_API_URL = originalEnv
  })

  test('falls back to default URL when env var not set', async () => {
    const originalEnv = process.env.NEXT_PUBLIC_LANGGRAPH_API_URL
    delete process.env.NEXT_PUBLIC_LANGGRAPH_API_URL

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => []
    })

    await testLangGraphConnection()

    expect(global.fetch).toHaveBeenCalledWith('http://localhost:9876/assistants')
    
    // Restore original environment
    process.env.NEXT_PUBLIC_LANGGRAPH_API_URL = originalEnv
  })

  test('handles thread creation failure', async () => {
    ;(global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ id: 'test-assistant-1' }]
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request'
      })

    const result = await testLangGraphConnection()
    expect(result).toBe(false)
    
    expect(global.fetch).toHaveBeenCalledTimes(2)
  })

  test('handles message sending when assistants are available', async () => {
    ;(global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ id: 'test-assistant-1' }]
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ thread_id: 'test-thread-123' })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: 'test-run-456' })
      })

    const result = await testLangGraphConnection()
    expect(result).toBe(true)
    
    // Should make all three API calls
    expect(global.fetch).toHaveBeenCalledTimes(3)
    
    // Check that message sending call was made
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/threads\/test-thread-123\/runs$/),
      expect.objectContaining({
        method: 'POST'
      })
    )
  })
})