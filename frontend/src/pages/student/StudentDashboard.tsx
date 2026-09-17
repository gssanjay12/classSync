import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Vote,
  CheckCircle2,
  Clock,
  Plus,
  BookOpen,
  ArrowRight,
  TrendingUp,
  AlertCircle,
} from 'lucide-react';
import api from '../../api/client';
import { StudentDashboardStats, ClassItem, Poll } from '../../types';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';
import { Badge } from '../../components/common/Badge';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';

export const StudentDashboard: React.FC = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [classCode, setClassCode] = useState('');
  const [isJoinModalOpen, setIsJoinModalOpen] = useState(false);

  // 1. Dashboard Stats
  const { data: stats, isLoading: statsLoading } = useQuery<StudentDashboardStats>({
    queryKey: ['student-dashboard-stats'],
    queryFn: async () => {
      const res = await api.get('/dashboards/student');
      return res.data;
    },
  });

  // 2. Enrolled Classes
  const { data: classes, isLoading: classesLoading } = useQuery<ClassItem[]>({
    queryKey: ['student-classes'],
    queryFn: async () => {
      const res = await api.get('/classes');
      return res.data;
    },
  });

  // Join Class Mutation
  const joinClassMutation = useMutation({
    mutationFn: async (code: string) => {
      const res = await api.post('/classes/join', { class_code: code });
      return res.data;
    },
    onSuccess: (newClass) => {
      queryClient.invalidateQueries({ queryKey: ['student-classes'] });
      queryClient.invalidateQueries({ queryKey: ['student-dashboard-stats'] });
      setIsJoinModalOpen(false);
      setClassCode('');
      success(`Successfully joined ${newClass.name}!`);
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail || 'Failed to join class. Check code and try again.';
      toastError(detail);
    },
  });

  const handleJoinClass = (e: React.FormEvent) => {
    e.preventDefault();
    if (!classCode.trim()) return;
    joinClassMutation.mutate(classCode.trim().toUpperCase());
  };

  if (statsLoading || classesLoading) {
    return <LoadingSpinner message="Loading your dashboard..." />;
  }

  return (
    <div className="space-y-8">
      {/* Welcome & Action Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-3xl bg-linear-to-r from-indigo-900 to-indigo-700 text-white shadow-lg shadow-indigo-950/10">
        <div>
          <span className="px-3 py-1 rounded-full bg-white/15 text-indigo-100 text-xs font-semibold backdrop-blur-xs">
            Student Portal
          </span>
          <h1 className="text-2xl font-bold mt-2">Welcome back, {user?.name}!</h1>
          <p className="text-sm text-indigo-100/80 mt-0.5">
            {user?.student_profile
              ? `${user.student_profile.register_number} • ${user.student_profile.department} (Year ${user.student_profile.year} - Sec ${user.student_profile.section})`
              : 'Enrolled Student'}
          </p>
        </div>
        <button
          onClick={() => setIsJoinModalOpen(true)}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-white text-indigo-900 text-sm font-semibold rounded-xl hover:bg-indigo-50 shadow-sm transition-all active:scale-95 shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>Join Class</span>
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Polls</span>
            <Vote className="w-4 h-4 text-indigo-600" />
          </div>
          <p className="text-2xl font-black text-slate-900">{stats?.active_polls_count ?? 0}</p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Completed</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-black text-emerald-600">{stats?.completed_polls_count ?? 0}</p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pending</span>
            <Clock className="w-4 h-4 text-rose-500" />
          </div>
          <p className="text-2xl font-black text-rose-600">{stats?.pending_polls_count ?? 0}</p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Completion Rate</span>
            <TrendingUp className="w-4 h-4 text-purple-600" />
          </div>
          <p className="text-2xl font-black text-purple-600">{stats?.completion_rate ?? 0}%</p>
        </div>
      </div>

      {/* Enrolled Classes List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-900">Enrolled Classes</h2>
          <Link to="/student/polls" className="text-xs font-semibold text-indigo-600 hover:text-indigo-700">
            View all polls →
          </Link>
        </div>

        {!classes || classes.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="No classes joined yet"
            description="Enter a 6-character class code from your teacher or class rep to enroll."
            action={{
              label: 'Join Your First Class',
              onClick: () => setIsJoinModalOpen(true),
            }}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {classes.map((cls) => (
              <div
                key={cls.id}
                className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs hover:border-indigo-100 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">
                      {cls.class_code}
                    </span>
                    {cls.is_rep && <Badge variant="rep">CLASS REP</Badge>}
                  </div>
                  <h3 className="text-lg font-bold text-slate-900">{cls.name}</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    {cls.department} • Year {cls.year} (Sec {cls.section})
                  </p>
                </div>

                <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                  <span>{cls.active_polls} Active Polls</span>
                  <Link
                    to="/student/polls"
                    className="font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                  >
                    <span>Polls</span>
                    <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Join Class Modal */}
      {isJoinModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-100">
            <h3 className="text-lg font-bold text-slate-900 mb-1">Join a Class</h3>
            <p className="text-xs text-slate-500 mb-5">Ask your teacher or class representative for the 6-character code.</p>

            <form onSubmit={handleJoinClass} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Class Code
                </label>
                <input
                  type="text"
                  required
                  maxLength={10}
                  value={classCode}
                  onChange={(e) => setClassCode(e.target.value.toUpperCase())}
                  placeholder="ADSA27"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-center text-lg font-mono font-bold tracking-widest uppercase focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsJoinModalOpen(false)}
                  className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={joinClassMutation.isPending || !classCode.trim()}
                  className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl disabled:opacity-50"
                >
                  {joinClassMutation.isPending ? 'Joining...' : 'Join Class'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
