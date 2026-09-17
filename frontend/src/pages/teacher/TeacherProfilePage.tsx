import React from 'react';
import { School, Mail, Shield, BookOpen } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { Badge } from '../../components/common/Badge';

export const TeacherProfilePage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Faculty Profile</h1>
        <p className="text-sm text-slate-500">Your faculty credentials and assigned classes.</p>
      </div>

      <div className="bg-white rounded-3xl p-8 border border-slate-100 shadow-xs flex items-center gap-6">
        <div className="w-20 h-20 rounded-2xl bg-indigo-600 text-white flex items-center justify-center font-bold text-3xl shadow-lg shadow-indigo-200">
          {user?.name.charAt(0).toUpperCase()}
        </div>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-2xl font-bold text-slate-900">{user?.name}</h2>
            <Badge variant="teacher">TEACHER</Badge>
          </div>
          <p className="text-sm text-slate-500">{user?.email}</p>
          <div className="mt-3 flex items-center gap-2 text-xs font-semibold">
            <span className="px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700">
              Employee ID: {user?.teacher_profile?.employee_id || 'N/A'}
            </span>
            <span className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700">
              Dept: {user?.teacher_profile?.department || 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {/* Assigned Classes */}
      <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-xs">
        <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-indigo-600" />
          <span>Assigned Classes</span>
        </h3>
        {user?.teacher_classes && user.teacher_classes.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {user.teacher_classes.map((c) => (
              <span key={c.class_id} className="px-3 py-1.5 rounded-xl bg-slate-100 text-slate-800 text-xs font-bold">
                {c.class_name}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-400">No classes assigned yet.</p>
        )}
      </div>
    </div>
  );
};
