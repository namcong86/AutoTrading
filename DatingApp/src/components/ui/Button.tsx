import React from 'react';
import Link from 'next/link';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'outline';
    href?: string;
}

export default function Button({
    children,
    variant = 'primary',
    href,
    className = '',
    ...props
}: ButtonProps) {
    const baseClass = `btn btn-${variant} ${className}`;

    if (href) {
        return (
            <Link href={href} className={baseClass}>
                {children}
            </Link>
        );
    }

    return (
        <button className={baseClass} {...props}>
            {children}
        </button>
    );
}
