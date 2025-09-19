import React from 'react';
import { render, screen } from '@testing-library/react';
import Typography from '../Typography';

describe('Typography Component', () => {
  it('renders h1 variant correctly', () => {
    render(<Typography variant='h1'>Heading 1</Typography>);
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toBeInTheDocument();
    expect(heading).toHaveTextContent('Heading 1');
    expect(heading).toHaveClass('text-3xl', 'font-bold');
  });

  it('renders h2 variant correctly', () => {
    render(<Typography variant='h2'>Heading 2</Typography>);
    const heading = screen.getByRole('heading', { level: 2 });
    expect(heading).toBeInTheDocument();
    expect(heading).toHaveTextContent('Heading 2');
    expect(heading).toHaveClass('text-2xl', 'font-semibold');
  });

  it('renders h3 variant correctly', () => {
    render(<Typography variant='h3'>Heading 3</Typography>);
    const heading = screen.getByRole('heading', { level: 3 });
    expect(heading).toBeInTheDocument();
    expect(heading).toHaveTextContent('Heading 3');
    expect(heading).toHaveClass('text-xl', 'font-medium');
  });

  it('renders p variant correctly', () => {
    render(<Typography variant='p'>Paragraph text</Typography>);
    const paragraph = screen.getByText('Paragraph text');
    expect(paragraph).toBeInTheDocument();
    expect(paragraph.tagName).toBe('P');
    expect(paragraph).toHaveClass('text-base');
  });

  it('renders span variant correctly', () => {
    render(<Typography variant='span'>Span text</Typography>);
    const span = screen.getByText('Span text');
    expect(span).toBeInTheDocument();
    expect(span.tagName).toBe('SPAN');
    expect(span).toHaveClass('text-base');
  });

  it('applies custom className', () => {
    render(
      <Typography variant='p' className='custom-class'>
        Custom styled text
      </Typography>
    );
    const element = screen.getByText('Custom styled text');
    expect(element).toHaveClass('custom-class');
    expect(element).toHaveClass('text-base'); // Still has base classes
  });

  it('handles React node children', () => {
    render(
      <Typography variant='p'>
        <strong>Bold</strong> and <em>italic</em> text
      </Typography>
    );

    // Use a more specific selector for the paragraph
    const paragraph = document.querySelector('p');
    expect(paragraph).toBeInTheDocument();
    expect(paragraph?.textContent).toBe('Bold and italic text');
    expect(paragraph?.querySelector('strong')).toHaveTextContent('Bold');
    expect(paragraph?.querySelector('em')).toHaveTextContent('italic');
  });

  it('combines base classes with custom classes properly', () => {
    render(
      <Typography variant='h1' className='text-red-500 mt-4'>
        Styled heading
      </Typography>
    );

    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toHaveClass(
      'text-3xl',
      'font-bold',
      'text-red-500',
      'mt-4'
    );
  });

  it('handles empty className gracefully', () => {
    render(
      <Typography variant='p' className=''>
        Plain text
      </Typography>
    );
    const element = screen.getByText('Plain text');
    expect(element).toHaveClass('text-base');
    expect(element.className).not.toContain('undefined');
  });

  it('trims className properly', () => {
    render(
      <Typography variant='p' className='  extra-space  '>
        Text
      </Typography>
    );
    const element = screen.getByText('Text');
    expect(element.className).not.toMatch(/^\s|\s$/); // No leading/trailing spaces
  });
});
