import React from 'react'
import { render, screen } from '@testing-library/react'
import Typography from '@/components/Typography'

describe('Typography Component', () => {
  test('renders h1 variant correctly', () => {
    render(
      <Typography variant="h1" className="test-class">
        Test Heading 1
      </Typography>
    )
    
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toBeInTheDocument()
    expect(heading).toHaveTextContent('Test Heading 1')
    expect(heading).toHaveClass('text-3xl', 'font-bold', 'test-class')
  })

  test('renders h2 variant correctly', () => {
    render(
      <Typography variant="h2">
        Test Heading 2
      </Typography>
    )
    
    const heading = screen.getByRole('heading', { level: 2 })
    expect(heading).toBeInTheDocument()
    expect(heading).toHaveTextContent('Test Heading 2')
    expect(heading).toHaveClass('text-2xl', 'font-semibold')
  })

  test('renders h3 variant correctly', () => {
    render(
      <Typography variant="h3">
        Test Heading 3
      </Typography>
    )
    
    const heading = screen.getByRole('heading', { level: 3 })
    expect(heading).toBeInTheDocument()
    expect(heading).toHaveTextContent('Test Heading 3')
    expect(heading).toHaveClass('text-xl', 'font-medium')
  })

  test('renders p variant correctly', () => {
    render(
      <Typography variant="p">
        Test paragraph text
      </Typography>
    )
    
    const paragraph = screen.getByText('Test paragraph text')
    expect(paragraph).toBeInTheDocument()
    expect(paragraph.tagName).toBe('P')
    expect(paragraph).toHaveClass('text-base')
  })

  test('renders span variant correctly', () => {
    render(
      <Typography variant="span">
        Test span text
      </Typography>
    )
    
    const span = screen.getByText('Test span text')
    expect(span).toBeInTheDocument()
    expect(span.tagName).toBe('SPAN')
    expect(span).toHaveClass('text-base')
  })

  test('applies custom className correctly', () => {
    render(
      <Typography variant="p" className="custom-class another-class">
        Test text
      </Typography>
    )
    
    const element = screen.getByText('Test text')
    expect(element).toHaveClass('text-base', 'custom-class', 'another-class')
  })

  test('renders without className prop', () => {
    render(
      <Typography variant="p">
        Test text without className
      </Typography>
    )
    
    const element = screen.getByText('Test text without className')
    expect(element).toBeInTheDocument()
    expect(element).toHaveClass('text-base')
  })

  test('handles React children correctly', () => {
    render(
      <Typography variant="p">
        <span>Nested content</span> with text
      </Typography>
    )
    
    const paragraph = screen.getByText(/Nested content.*with text/)
    expect(paragraph).toBeInTheDocument()
    
    const nestedSpan = screen.getByText('Nested content')
    expect(nestedSpan.tagName).toBe('SPAN')
  })
})