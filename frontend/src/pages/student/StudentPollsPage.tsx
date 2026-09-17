import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Vote, Clock, ArrowRight, CheckCircle2, School } from 'lucide-react';
import api from '../../api/client';
import { ClassItem, Poll } from '../../types';
import { Badge } from '../../components/common/Badge';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';

export const StudentPollsPage: React.FC = () => {
  // Fetch enrolled classes
  const { data: classes, isLoading: classesLoading } = useQuery<ClassItem[]>({
    queryKey: ['student-classes'],
    queryFn: async () => {
      const res = await api.get('/classes');
      return res.data;
    },
  });

  // Fetch polls from all classes
  const { data: polls, isLoading: pollsLoading } = useQuery<Poll[]>({
    queryKey: ['all-student-polls', classes?.map((c) => c.id)],
    queryFn: async () => {
      if (!classes || classes.length === 0) return [];
      const promises = classes.map((c) => api.get(`/classes/${c.id}/polls`));
      const results = await Promise.all(promises);
      return results.flatMap((r) => r.data);
    },
    enabled: Boolean(classes && classes.length > 0),
  });

  if (classesLoading || pollsLoading) {
    return <LoadingSpinner message="Loading polls..." />;
  }

  const activePolls = polls?.filter((p) => !p.is_closed) || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Active Class Polls</h1>
        <p className="text-sm text-slate-500">Respond to open questions posted by your teachers and representatives.</p>
      </div>

      {activePolls.length === 0 ? (
        <EmptyState
          icon={Vote}
          title="No active polls right now"
          description="When your teacher or class rep shares a poll in WhatsApp or posts it here, it will show up instantly."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {activePolls.map((poll) => (
            <div
              key={poll.id}
              className="p-6 rounded-3xl bg-white border border-slate-100 shadow-xs hover:border-indigo-100 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700">
                    {poll.class_name}
                  </span>
                  <Badge variant={poll.has_responded ? 'done' : 'not-done'}>
                    {poll.has_responded ? '✓ DONE' : 'NOT DONE'}
                  </Badge>
                </div>

                <h2 className="text-lg font-bold text-slate-900 leading-snug">{poll.question}</h2>

                <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  <span>
                    Deadline: {new Date(poll.deadline).toLocaleDateString([], { month: 'short', day: 'numeric' })}{' '}
                    {new Date(poll.deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
                <span className="text-xs text-slate-400">By {poll.creator_name}</span>
                <Link
                  to={`/poll/${poll.public_id}`}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-all active:scale-95"
                >
                  <span>{poll.has_responded ? 'View / Change' : 'Answer Poll'}</span>
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
