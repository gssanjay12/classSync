import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ShieldCheck, BookOpen, Users, Vote, ArrowRight } from 'lucide-react';
import api from '../../api/client';
import { ClassItem } from '../../types';
import { useAuth } from '../../contexts/AuthContext';
import { Badge } from '../../components/common/Badge';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';

export const RepDashboard: React.FC = () => {
  const { user } = useAuth();

  const { data: classes, isLoading } = useQuery<ClassItem[]>({
    queryKey: ['rep-classes'],
    queryFn: async () => {
      const res = await api.get('/classes');
      return res.data;
    },
  });

  if (isLoading) {
    return <LoadingSpinner message="Loading representative console..." />;
  }

  const repClasses = classes?.filter((c) => c.is_rep) || [];

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="p-6 md:p-8 rounded-3xl bg-linear-to-r from-teal-900 to-slate-900 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="px-3 py-1 rounded-full bg-teal-500/20 text-teal-300 text-xs font-semibold backdrop-blur-xs border border-teal-500/30">
              Class Representative Console
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold">Welcome, {user?.name}!</h1>
          <p className="text-sm text-teal-100/80 mt-1">
            Track student participation and facilitate WhatsApp coordination for your assigned classes.
          </p>
        </div>

        <Link
          to="/student/dashboard"
          className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white text-xs font-semibold rounded-xl border border-white/20 transition-all"
        >
          Switch to Student View →
        </Link>
      </div>

      {/* REP Classes */}
      <div>
        <h2 className="text-lg font-bold text-slate-900 mb-4">Your Representative Assignments</h2>

        {repClasses.length === 0 ? (
          <EmptyState
            icon={ShieldCheck}
            title="No class representative assignments"
            description="You are not currently designated as a REP for any active class."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {repClasses.map((cls) => (
              <div
                key={cls.id}
                className="p-6 rounded-3xl bg-white border border-slate-100 shadow-xs hover:border-teal-200 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-lg bg-teal-50 text-teal-700">
                      Code: {cls.class_code}
                    </span>
                    <Badge variant="rep">REP ACCESS</Badge>
                  </div>

                  <h3 className="text-xl font-bold text-slate-900">{cls.name}</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    {cls.department} • Year {cls.year} (Sec {cls.section})
                  </p>

                  <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                    <div className="p-3 rounded-2xl bg-slate-50">
                      <span className="text-slate-500 block">Class Size</span>
                      <span className="font-bold text-slate-800 text-sm">{cls.total_students} Students</span>
                    </div>
                    <div className="p-3 rounded-2xl bg-slate-50">
                      <span className="text-slate-500 block">Active Polls</span>
                      <span className="font-bold text-slate-800 text-sm">{cls.active_polls} Active</span>
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-end">
                  <Link
                    to={`/rep/classes/${cls.id}`}
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-all active:scale-95"
                  >
                    <span>Manage Class & Polls</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
