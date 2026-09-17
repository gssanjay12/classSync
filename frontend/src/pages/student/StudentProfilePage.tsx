import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { User, Mail, GraduationCap, School, CheckCircle2, Shield, Calendar, Edit2 } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';
import api from '../../api/client';
import { StudentDashboardStats } from '../../types';
import { Badge } from '../../components/common/Badge';

export const StudentProfilePage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const { success, error: toastError } = useToast();

  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(user?.name || '');
  const [section, setSection] = useState(user?.student_profile?.section || '');

  // Fetch stats for profile
  const { data: stats } = useQuery<StudentDashboardStats>({
    queryKey: ['student-dashboard-stats'],
    queryFn: async () => {
      const res = await api.get('/dashboards/student');
      return res.data;
    },
  });

  const updateProfileMutation = useMutation({
    mutationFn: async () => {
      const res = await api.patch('/users/me', {
        name,
        section: section.toUpperCase(),
      });
      return res.data;
    },
    onSuccess: async () => {
      await refreshUser();
      setIsEditing(false);
      success('Profile updated successfully!');
    },
    onError: (err: any) => {
      toastError(err.response?.data?.detail || 'Failed to update profile.');
    },
  });

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Student Profile</h1>
        <p className="text-sm text-slate-500">Your verified academic identity and participation metrics.</p>
      </div>

      {/* Main Profile Header Card */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-100 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div className="flex items-center gap-5">
          <div className="w-18 h-18 rounded-2xl bg-indigo-600 text-white flex items-center justify-center font-bold text-2xl shadow-lg shadow-indigo-200">
            {user?.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-900">{user?.name}</h2>
              {user?.rep_classes && user.rep_classes.length > 0 ? (
                <Badge variant="rep">REP ({user.rep_classes.length} class{user.rep_classes.length > 1 ? 'es' : ''})</Badge>
              ) : (
                <Badge variant="student">Student</Badge>
              )}
            </div>
            <p className="text-sm text-slate-500 mt-0.5">{user?.email}</p>
            <div className="flex items-center gap-3 mt-2 text-xs font-semibold text-indigo-700">
              <span className="px-2.5 py-1 bg-indigo-50 rounded-lg">
                Reg: {user?.student_profile?.register_number || 'N/A'}
              </span>
              <span className="px-2.5 py-1 bg-slate-100 text-slate-700 rounded-lg">
                Status: {user?.status}
              </span>
            </div>
          </div>
        </div>

        <button
          onClick={() => setIsEditing(!isEditing)}
          className="inline-flex items-center gap-1.5 px-4 py-2 border border-slate-200 hover:bg-slate-50 rounded-xl text-xs font-semibold text-slate-700 transition-colors"
        >
          <Edit2 className="w-3.5 h-3.5" />
          <span>{isEditing ? 'Cancel Edit' : 'Edit Profile'}</span>
        </button>
      </div>

      {/* Edit Form Modal/Card if toggled */}
      {isEditing && (
        <div className="p-6 rounded-2xl bg-white border border-indigo-100 shadow-xs animate-in fade-in">
          <h3 className="text-sm font-bold text-slate-900 mb-4">Edit Profile Information</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Section</label>
              <input
                type="text"
                value={section}
                maxLength={5}
                onChange={(e) => setSection(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm uppercase"
              />
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <button
              onClick={() => updateProfileMutation.mutate()}
              disabled={updateProfileMutation.isPending}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl"
            >
              {updateProfileMutation.isPending ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      )}

      {/* Detailed Info & Participation Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-xs space-y-4">
          <h3 className="text-base font-bold text-slate-900">Academic Details</h3>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b border-slate-50">
              <span className="text-slate-500">Department</span>
              <span className="font-semibold text-slate-800">{user?.student_profile?.department}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-50">
              <span className="text-slate-500">Academic Year</span>
              <span className="font-semibold text-slate-800">Year {user?.student_profile?.year}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-50">
              <span className="text-slate-500">Section</span>
              <span className="font-semibold text-slate-800">Sec {user?.student_profile?.section}</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-500">Account Created</span>
              <span className="font-semibold text-slate-800">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-xs space-y-4">
          <h3 className="text-base font-bold text-slate-900">Participation Analytics</h3>

          <div className="grid grid-cols-2 gap-3 pt-1">
            <div className="p-4 rounded-2xl bg-indigo-50/50 border border-indigo-100">
              <span className="text-xs font-medium text-slate-500">Completed Polls</span>
              <p className="text-2xl font-black text-indigo-700 mt-1">{stats?.completed_polls_count ?? 0}</p>
            </div>
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <span className="text-xs font-medium text-slate-500">Pending Polls</span>
              <p className="text-2xl font-black text-slate-800 mt-1">{stats?.pending_polls_count ?? 0}</p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider">Overall Completion</span>
              <p className="text-xs text-emerald-700 mt-0.5">Reliability score in enrolled classes</p>
            </div>
            <span className="text-2xl font-black text-emerald-700">{stats?.completion_rate ?? 0}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};
