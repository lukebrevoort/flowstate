import config from '@/lib/config'

describe('Configuration', () => {
  const originalEnv = process.env.NODE_ENV

  afterEach(() => {
    process.env.NODE_ENV = originalEnv
  })

  test('uses development config in development environment', () => {
    process.env.NODE_ENV = 'development'
    
    // Re-import to get fresh config
    jest.resetModules()
    const { default: devConfig } = require('@/lib/config')
    
    expect(devConfig.apiUrl).toBe('http://localhost:5001')
    expect(devConfig.langGraphUrl).toBe('http://localhost:9876')
  })

  test('uses production config in production environment', () => {
    process.env.NODE_ENV = 'production'
    
    // Mock environment variables
    process.env.NEXT_PUBLIC_API_URL = 'https://custom-api.com'
    process.env.NEXT_PUBLIC_LANGGRAPH_URL = 'https://custom-langgraph.com'
    
    jest.resetModules()
    const { default: prodConfig } = require('@/lib/config')
    
    expect(prodConfig.apiUrl).toBe('https://custom-api.com')
    expect(prodConfig.langGraphUrl).toBe('https://custom-langgraph.com')
  })

  test('falls back to default production URLs when env vars not set', () => {
    process.env.NODE_ENV = 'production'
    delete process.env.NEXT_PUBLIC_API_URL
    delete process.env.NEXT_PUBLIC_LANGGRAPH_URL
    
    jest.resetModules()
    const { default: prodConfig } = require('@/lib/config')
    
    expect(prodConfig.apiUrl).toBe('https://flowstate-xqoe.onrender.com')
    expect(prodConfig.langGraphUrl).toBe('https://flowstate-xqoe.onrender.com')
  })

  test('config object has required properties', () => {
    expect(config).toHaveProperty('apiUrl')
    expect(config).toHaveProperty('langGraphUrl')
    expect(typeof config.apiUrl).toBe('string')
    expect(typeof config.langGraphUrl).toBe('string')
    expect(config.apiUrl.length).toBeGreaterThan(0)
    expect(config.langGraphUrl.length).toBeGreaterThan(0)
  })

  test('URLs are valid format', () => {
    const urlPattern = /^https?:\/\/[^\s/$.?#].[^\s]*$/
    
    expect(config.apiUrl).toMatch(urlPattern)
    expect(config.langGraphUrl).toMatch(urlPattern)
  })
})