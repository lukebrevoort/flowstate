/**
 * Simple test to verify Jest is working correctly
 */

describe('Basic Frontend Tests', () => {
  test('Jest is working correctly', () => {
    expect(1 + 1).toBe(2)
  })

  test('Environment variables are available', () => {
    expect(process.env.NEXT_PUBLIC_LANGGRAPH_API_URL).toBeDefined()
    expect(process.env.NEXT_PUBLIC_API_URL).toBeDefined()
  })

  test('JavaScript features work correctly', () => {
    const testArray = [1, 2, 3, 4, 5]
    const doubled = testArray.map(x => x * 2)
    
    expect(doubled).toEqual([2, 4, 6, 8, 10])
  })

  test('Async/await works correctly', async () => {
    const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))
    
    const start = Date.now()
    await delay(10)
    const end = Date.now()
    
    expect(end - start).toBeGreaterThanOrEqual(10)
  })

  test('Mock functions work correctly', () => {
    const mockFn = jest.fn()
    mockFn('test')
    mockFn('test2')
    
    expect(mockFn).toHaveBeenCalledTimes(2)
    expect(mockFn).toHaveBeenCalledWith('test')
    expect(mockFn).toHaveBeenCalledWith('test2')
  })

  test('Object spread operator works', () => {
    const original = { a: 1, b: 2 }
    const updated = { ...original, c: 3 }
    
    expect(updated).toEqual({ a: 1, b: 2, c: 3 })
    expect(original).toEqual({ a: 1, b: 2 })
  })

  test('Template literals work', () => {
    const name = 'FlowState'
    const message = `Welcome to ${name}!`
    
    expect(message).toBe('Welcome to FlowState!')
  })

  test('JSON operations work', () => {
    const data = { test: 'value', number: 42 }
    const jsonString = JSON.stringify(data)
    const parsed = JSON.parse(jsonString)
    
    expect(parsed).toEqual(data)
  })
})