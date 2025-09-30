import { ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
}

export function Button({ 
  children, 
  className, 
  variant = 'primary', 
  ...props 
}: ButtonProps) {
  return (
    <button
      className={cn(
        'px-4 py-2 rounded-full font-medium transition-all duration-200',
        {
          'bg-gradient-to-r from-green-500 to-emerald-500 text-white hover:opacity-90':
            variant === 'primary',
          'border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-800':
            variant === 'secondary',
          'bg-red-500 text-white hover:bg-red-600':
            variant === 'danger',
        },
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}