import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { UserRole } from '../../types';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <LoadingSpinner message="Checking authorization..." />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (user.status === 'PENDING') {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-slate-50">
        <div className="max-w-md w-full p-8 bg-white rounded-2xl shadow-sm border border-amber-200 text-center">
          <div className="w-12 h-12 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center mx-auto mb-4">
            ⏳
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">Account Pending Approval</h2>
          <p className="text-sm text-slate-600 mb-6">
            Your teacher account has been submitted and is currently awaiting administrator verification.
          </p>
          <button
            onClick={() => {
              localStorage.clear();
              window.location.href = '/login';
            }}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg"
          >
            Log out
          </button>
        </div>
      </div>
    );
  }

  if (allowedRoles) {
    const isFaculty = user.role === 'FACULTY' || (user.role as string) === 'TEACHER';
    const isStudent = user.role === 'STUDENT';
    const isAllowed = 
      (isFaculty && (allowedRoles.includes('FACULTY') || (allowedRoles as string[]).includes('TEACHER'))) ||
      (isStudent && allowedRoles.includes('STUDENT'));

    if (!isAllowed) {
      return <Navigate to="/login" replace />;
    }
  }

  return <>{children}</>;
};
