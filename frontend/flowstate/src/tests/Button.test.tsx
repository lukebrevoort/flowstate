import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import Button from '@/components/Button'

describe('Button Component', () => {
  test('renders button with children', () => {
    render(
      <Button>Click me</Button>
    )
    
    const button = screen.getByRole('button')
    expect(button).toBeInTheDocument()
    expect(button).toHaveTextContent('Click me')
  })

  test('handles onClick event', () => {
    const handleClick = jest.fn()
    render(
      <Button onClick={handleClick}>
        Click me
      </Button>
    )
    
    const button = screen.getByRole('button')
    fireEvent.click(button)
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  test('applies default button type', () => {
    render(
      <Button>Default button</Button>
    )
    
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('type', 'button')
  })

  test('applies custom button type', () => {
    render(
      <Button type="submit">Submit button</Button>
    )
    
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('type', 'submit')
  })

  test('handles disabled state', () => {
    const handleClick = jest.fn()
    render(
      <Button disabled onClick={handleClick}>
        Disabled button
      </Button>
    )
    
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button).toHaveClass('opacity-50', 'cursor-not-allowed')
    
    fireEvent.click(button)
    expect(handleClick).not.toHaveBeenCalled()
  })

  test('applies default styling classes', () => {
    render(
      <Button>Styled button</Button>
    )
    
    const button = screen.getByRole('button')
    expect(button).toHaveClass(
      'px-4',
      'py-2', 
      'rounded-md',
      'font-medium',
      'transition-all',
      'duration-200',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-offset-2',
      'bg-flowstate-accent',
      'text-white',
      'hover:bg-opacity-90',
      'focus:ring-flowstate-accent'
    )
  })

  test('applies custom className', () => {
    render(
      <Button className="custom-class">
        Custom styled button
      </Button>
    )
    
    const button = screen.getByRole('button')
    expect(button).toHaveClass('custom-class')
    expect(button).toHaveClass('px-4') // should still have base classes
  })

  test('combines multiple className props correctly', () => {
    render(
      <Button className="custom-1 custom-2">
        Multi-class button
      </Button>
    )
    
    const button = screen.getByRole('button')
    expect(button).toHaveClass('custom-1', 'custom-2', 'px-4', 'py-2')
  })

  test('disabled button has correct styling', () => {
    render(
      <Button disabled>
        Disabled styled button
      </Button>
    )
    
    const button = screen.getByRole('button')
    expect(button).toHaveClass('opacity-50', 'cursor-not-allowed')
    expect(button).not.toHaveClass('bg-flowstate-accent') // disabled styling overrides
  })

  test('renders without onClick handler', () => {
    render(
      <Button>No handler button</Button>
    )
    
    const button = screen.getByRole('button')
    expect(button).toBeInTheDocument()
    
    // Should not throw error when clicked
    expect(() => fireEvent.click(button)).not.toThrow()
  })

  test('handles complex children content', () => {
    render(
      <Button>
        <span>Icon</span> Button Text
      </Button>
    )
    
    const button = screen.getByRole('button')
    expect(button).toBeInTheDocument()
    expect(screen.getByText('Icon')).toBeInTheDocument()
    expect(screen.getByText(/Button Text/)).toBeInTheDocument()
  })
})