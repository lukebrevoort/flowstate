import React from 'react';

interface TypographyProps {
  variant: 'h1' | 'h2' | 'h3' | 'p' | 'span';
  children: React.ReactNode;
  className?: string;
}

const Typography: React.FC<TypographyProps> = ({
  variant,
  children,
  className = '',
}) => {
  const baseClasses = {
    h1: 'text-3xl font-bold',
    h2: 'text-2xl font-semibold',
    h3: 'text-xl font-medium',
    p: 'text-base',
    span: 'text-base',
  };

  const combinedClassName = `${baseClasses[variant]} ${className}`.trim();

  switch (variant) {
    case 'h1':
      return <h1 className={combinedClassName}>{children}</h1>;
    case 'h2':
      return <h2 className={combinedClassName}>{children}</h2>;
    case 'h3':
      return <h3 className={combinedClassName}>{children}</h3>;
    case 'p':
      return <p className={combinedClassName}>{children}</p>;
    case 'span':
      return <span className={combinedClassName}>{children}</span>;
    default:
      return <p className={combinedClassName}>{children}</p>;
  }
};

export default Typography;
