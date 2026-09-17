import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { BookOpen, Users, Vote, ArrowRight } from 'lucide-react';
import api from '../../api/client';
import { ClassItem } from '../../types';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';

export const TeacherClassesPage: React.FC = () => {
  const { data: classes, isLoading } = useQuery<ClassItem[]>({
    queryKey: ['teacher-classes'],
    queryFn: async () => {
      const res = await api.get('/classes');
      return res.data;
    },
  });

  if (isLoading) {
    return <LoadingSpinner message="Loading classes..." />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">My Classes</h1>
        <p className="text-sm text-slate-500">Classes assigned to you for student polling and tracking.</p>
      </div>

      {!classes || classes.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="No classes assigned"
          description="You are not assigned to any classes yet. Please contact the administrator."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {classes.map((cls) => (
            <div
              key={cls.id}
              className="p-6 rounded-3xl bg-white border border-slate-100 shadow-xs hover:border-indigo-100 transition-all flex flex-col justify-between"
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
                  <span>Open Class Workspace</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
