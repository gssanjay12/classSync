import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { History, CheckCircle2, XCircle, Clock } from 'lucide-react';
import api from '../../api/client';
import { StudentHistoryItem } from '../../types';
import { Badge } from '../../components/common/Badge';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';

export const StudentHistoryPage: React.FC = () => {
  const { data: history, isLoading } = useQuery<StudentHistoryItem[]>({
    queryKey: ['student-history'],
    queryFn: async () => {
      const res = await api.get('/dashboards/student/history');
      return res.data;
    },
  });

  if (isLoading) {
    return <LoadingSpinner message="Loading participation history..." />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Participation History</h1>
        <p className="text-sm text-slate-500">Record of your past poll responses across all enrolled classes.</p>
      </div>

      {!history || history.length === 0 ? (
        <EmptyState
          icon={History}
          title="No participation history yet"
          description="Polls you respond to or that reach their deadline will be archived here."
        />
      ) : (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Class & Question</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Your Response</th>
                  <th className="px-6 py-3.5">Submitted At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.map((item) => (
                  <tr key={item.poll_id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-4">
                      <span className="text-xs font-semibold text-indigo-600 block mb-0.5">
                        {item.class_name}
                      </span>
                      <span className="font-semibold text-slate-900 text-sm">{item.question}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant={item.is_done ? 'done' : 'not-done'}>
                        {item.is_done ? '✓ DONE' : 'MISSED'}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {item.selected_option_text ? (
                        <span className="font-medium text-slate-800 bg-slate-100 px-2.5 py-1 rounded-lg text-xs">
                          {item.selected_option_text}
                        </span>
                      ) : (
                        <span className="text-slate-400 text-xs italic">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-500">
                      {item.submitted_at ? (
                        new Date(item.submitted_at).toLocaleDateString([], {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
