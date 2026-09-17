import React from 'react';

interface BadgeProps {
  variant?: 'done' | 'not-done' | 'active' | 'closed' | 'pending' | 'admin' | 'teacher' | 'rep' | 'student' | 'default';
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ variant = 'default', children, className = '' }) => {
  const variantStyles = {
    done: 'bg-emerald-50 text-emerald-700 border-emerald-200 ring-1 ring-emerald-500/10',
    'not-done': 'bg-rose-50 text-rose-700 border-rose-200 ring-1 ring-rose-500/10',
    active: 'bg-indigo-50 text-indigo-700 border-indigo-200 ring-1 ring-indigo-500/10',
    closed: 'bg-slate-100 text-slate-700 border-slate-200',
    pending: 'bg-amber-50 text-amber-700 border-amber-200 ring-1 ring-amber-500/10',
    admin: 'bg-purple-50 text-purple-700 border-purple-200',
    teacher: 'bg-blue-50 text-blue-700 border-blue-200',
    rep: 'bg-teal-50 text-teal-700 border-teal-200',
    student: 'bg-slate-50 text-slate-700 border-slate-200',
    default: 'bg-slate-100 text-slate-800 border-slate-200',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
