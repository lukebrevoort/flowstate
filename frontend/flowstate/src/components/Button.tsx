import React from 'react';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
}

const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  className = '',
  disabled = false,
  type = 'button',
}) => {
  const baseClasses =
    'px-4 py-2 rounded-md font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2';
  const defaultClasses =
    'bg-flowstate-accent text-white hover:bg-opacity-90 focus:ring-flowstate-accent';
  const disabledClasses = 'opacity-50 cursor-not-allowed';

  const combinedClassName =
    `${baseClasses} ${disabled ? disabledClasses : defaultClasses} ${className}`.trim();

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={combinedClassName}
    >
      {children}
    </button>
  );
};

export default Button;
