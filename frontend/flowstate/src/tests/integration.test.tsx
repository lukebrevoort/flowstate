/**
 * Integration tests for the overall application flow
 */

describe('Application Integration', () => {
  test('environment variables are properly configured', () => {
    expect(process.env.NEXT_PUBLIC_LANGGRAPH_API_URL).toBeDefined()
    expect(process.env.NEXT_PUBLIC_API_URL).toBeDefined()
  })

  test('React components can be imported without errors', async () => {
    // Test that main components can be imported
    const Typography = await import('@/components/Typography')
    const Button = await import('@/components/Button')
    
    expect(Typography.default).toBeDefined()
    expect(Button.default).toBeDefined()
  })

  test('utility modules can be imported', async () => {
    const config = await import('@/lib/config')
    
    expect(config.default).toBeDefined()
    expect(typeof config.default).toBe('object')
  })

  test('test utilities work correctly', () => {
    // Test that our test setup is working
    expect(global.fetch).toBeDefined()
    expect(jest.fn).toBeDefined()
  })

  test('API URL configuration is consistent', async () => {
    const config = await import('@/lib/config')
    
    // URLs should be consistent with environment expectations
    if (process.env.NODE_ENV === 'production') {
      expect(config.default.apiUrl).toContain('https://')
      expect(config.default.langGraphUrl).toContain('https://')
    } else {
      expect(config.default.apiUrl).toContain('localhost')
      expect(config.default.langGraphUrl).toContain('localhost')
    }
  })

  test('test environment isolation', () => {
    // Ensure tests are running in isolation
    expect(process.env.NODE_ENV).not.toBe('production')
  })
})