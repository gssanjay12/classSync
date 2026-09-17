import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { BookOpen, Users, Vote, TrendingUp, ArrowRight, Plus } from 'lucide-react';
import api from '../../api/client';
import { TeacherDashboardStats, ClassItem } from '../../types';
import { useAuth } from '../../contexts/AuthContext';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';

export const TeacherDashboard: React.FC = () => {
  const { user } = useAuth();

  // 1. Teacher stats
  const { data: stats, isLoading: statsLoading } = useQuery<TeacherDashboardStats>({
    queryKey: ['teacher-dashboard-stats'],
    queryFn: async () => {
      const res = await api.get('/dashboards/teacher');
      return res.data;
    },
  });

  // 2. Assigned classes
  const { data: classes, isLoading: classesLoading } = useQuery<ClassItem[]>({
    queryKey: ['teacher-classes'],
    queryFn: async () => {
      const res = await api.get('/classes');
      return res.data;
    },
  });

  if (statsLoading || classesLoading) {
    return <LoadingSpinner message="Loading teacher dashboard..." />;
  }

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="p-6 md:p-8 rounded-3xl bg-linear-to-r from-slate-900 to-indigo-950 text-white shadow-xl shadow-slate-950/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-semibold backdrop-blur-xs border border-indigo-500/30">
            Teacher Console
          </span>
          <h1 className="text-2xl md:text-3xl font-bold mt-2">Welcome, {user?.name}!</h1>
          <p className="text-sm text-slate-300 mt-1">
            Manage your assigned classes, create WhatsApp-ready polls, and monitor live participation.
          </p>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">My Classes</span>
            <BookOpen className="w-4 h-4 text-indigo-600" />
          </div>
          <p className="text-2xl font-black text-slate-900">{stats?.my_classes_count ?? 0}</p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Students</span>
            <Users className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-2xl font-black text-slate-900">{stats?.total_students ?? 0}</p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Polls</span>
            <Vote className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-black text-emerald-600">{stats?.active_polls ?? 0}</p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Avg. Completion</span>
            <TrendingUp className="w-4 h-4 text-purple-600" />
          </div>
          <p className="text-2xl font-black text-purple-600">{stats?.average_completion_rate ?? 0}%</p>
        </div>
      </div>

      {/* Assigned Classes Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-900">Assigned Classes</h2>
        </div>

        {!classes || classes.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="No classes assigned"
            description="Contact your college administrator to be assigned to your subject or batch class groups."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {classes.map((cls) => (
              <div
                key={cls.id}
                className="p-6 rounded-3xl bg-white border border-slate-100 shadow-xs hover:shadow-md hover:border-indigo-100 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700">
                      Code: {cls.class_code}
                    </span>
                    <span className="text-xs text-slate-400">AY {cls.academic_year}</span>
                  </div>

                  <h3 className="text-xl font-bold text-slate-900">{cls.name}</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    {cls.department} • Year {cls.year} (Sec {cls.section})
                  </p>

                  <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2.5 rounded-xl bg-slate-50">
                      <span className="text-slate-500 block">Enrolled</span>
                      <span className="font-bold text-slate-800 text-sm">{cls.total_students} Students</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-50">
                      <span className="text-slate-500 block">Polls</span>
                      <span className="font-bold text-slate-800 text-sm">{cls.active_polls} Active</span>
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-end">
                  <Link
                    to={`/teacher/classes/${cls.id}`}
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-all active:scale-95"
                  >
                    <span>Manage Class</span>
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
