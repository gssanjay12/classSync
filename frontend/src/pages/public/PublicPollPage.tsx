import React, { useState } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Vote,
  CheckCircle2,
  Clock,
  AlertCircle,
  Lock,
  ArrowRight,
  School,
  Share2,
  Calendar,
} from 'lucide-react';
import api from '../../api/client';
import { Poll } from '../../types';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { Badge } from '../../components/common/Badge';

export const PublicPollPage: React.FC = () => {
  const { publicId } = useParams<{ publicId: string }>();
  const { user } = useAuth();
  const location = useLocation();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [selectedOptionId, setSelectedOptionId] = useState<number | null>(null);

  // Fetch public poll details
  const {
    data: poll,
    isLoading,
    error,
  } = useQuery<Poll>({
    queryKey: ['public-poll', publicId],
    queryFn: async () => {
      const res = await api.get(`/polls/public/${publicId}`);
      return res.data;
    },
    enabled: Boolean(publicId && user),
    retry: false,
  });

  // Submit response mutation
  const respondMutation = useMutation({
    mutationFn: async (optionId: number) => {
      if (!poll) return;
      const res = await api.post(`/polls/${poll.id}/respond`, {
        option_id: optionId,
      });
      return res.data;
    },
    onSuccess: (updatedPoll) => {
      queryClient.setQueryData(['public-poll', publicId], updatedPoll);
      queryClient.invalidateQueries({ queryKey: ['student-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['student-history'] });
      success('Your response has been saved! You are marked as DONE.');
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail || 'Failed to submit response. Please try again.';
      toastError(detail);
    },
  });

  // If not logged in
  if (!user) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center p-4">
        <div className="max-w-md w-full bg-white rounded-3xl p-8 shadow-xl shadow-slate-200/50 border border-slate-100 text-center">
          <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-5 shadow-inner">
            <Lock className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">Student Authentication Required</h2>
          <p className="text-sm text-slate-600 leading-relaxed mb-6">
            This poll was shared via WhatsApp. To record your response in the class roster and mark you as{' '}
            <span className="font-semibold text-emerald-600">DONE</span>, please sign in.
          </p>

          <div className="space-y-3">
            <Link
              to="/login"
              state={{ from: location }}
              className="w-full inline-flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-md shadow-indigo-100 transition-all active:scale-95"
            >
              <span>Sign In with College Account</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/register/student"
              className="w-full inline-flex items-center justify-center py-2.5 px-4 rounded-xl text-sm font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
            >
              Don't have an account? Register
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <LoadingSpinner message="Loading poll details..." />
      </div>
    );
  }

  // Handle errors (e.g. 403 not in class or 404 not found)
  if (error) {
    const errorMsg =
      (error as any).response?.data?.detail || 'Unable to access this poll. It may have expired or been removed.';
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center p-4">
        <div className="max-w-md w-full bg-white rounded-3xl p-8 shadow-xl shadow-slate-200/50 border border-rose-100 text-center">
          <div className="w-14 h-14 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">Access Restricted</h2>
          <p className="text-sm text-slate-600 leading-relaxed mb-6">{errorMsg}</p>
          <Link
            to="/student/dashboard"
            className="inline-flex items-center justify-center px-5 py-2.5 rounded-xl text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
          >
            Go to My Dashboard
          </Link>
        </div>
      </div>
    );
  }

  if (!poll) return null;

  const currentSelection = selectedOptionId ?? poll.selected_option_id ?? null;
  const isExpired = poll.is_closed;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentSelection) {
      toastError('Please select an option before submitting.');
      return;
    }
    respondMutation.mutate(currentSelection);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center py-8 px-4 sm:px-6">
      <div className="max-w-lg w-full">
        {/* Top Header Card */}
        <div className="text-center mb-6">
          <Link to="/" className="inline-flex items-center gap-2 mb-2">
            <div className="w-9 h-9 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold text-sm shadow-md shadow-indigo-200">
              CP
            </div>
            <span className="text-xl font-black text-slate-900 tracking-tight">ClassPoll</span>
          </Link>
        </div>

        {/* Main Poll Answering Card */}
        <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/60 border border-slate-100 overflow-hidden">
          {/* Class metadata banner */}
          <div className="p-6 bg-slate-50/70 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm">
                <School className="w-5 h-5" />
              </div>
              <div>
                <span className="font-bold text-slate-900 text-base">{poll.class_name}</span>
                <p className="text-xs text-slate-500">Created by {poll.creator_name}</p>
              </div>
            </div>
            <Badge variant={poll.has_responded ? 'done' : isExpired ? 'closed' : 'active'}>
              {poll.has_responded ? '✓ DONE' : isExpired ? 'CLOSED' : 'ACTIVE'}
            </Badge>
          </div>

          {/* Question & Options */}
          <form onSubmit={handleSubmit} className="p-6 md:p-8 space-y-6">
            <div>
              <h1 className="text-xl md:text-2xl font-extrabold text-slate-900 leading-snug tracking-tight">
                {poll.question}
              </h1>

              <div className="mt-3 flex items-center gap-4 text-xs text-slate-500">
                <span className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  <span>
                    Deadline: {new Date(poll.deadline).toLocaleDateString([], { month: 'short', day: 'numeric' })}{' '}
                    {new Date(poll.deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </span>
              </div>
            </div>

            {/* Answer Status Notice */}
            {poll.has_responded && (
              <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200/70 flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                <div className="text-xs text-emerald-800">
                  <p className="font-semibold">Your response is recorded.</p>
                  <p className="text-emerald-700">
                    You are verified as DONE on the teacher's roster.{' '}
                    {poll.allow_response_editing && !isExpired && 'You may update your response before the deadline.'}
                  </p>
                </div>
              </div>
            )}

            {isExpired && !poll.has_responded && (
              <div className="p-4 rounded-2xl bg-slate-100 border border-slate-200 text-xs text-slate-600 flex items-center gap-2.5">
                <Clock className="w-4 h-4 text-slate-500 shrink-0" />
                <span>This poll has reached its deadline and is no longer accepting submissions.</span>
              </div>
            )}

            {/* Option Radio Pills */}
            <div className="space-y-3">
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Select Your Answer
              </label>
              {poll.options.map((option) => {
                const isSelected = currentSelection === option.id;
                const canSelect = !isExpired && (!poll.has_responded || poll.allow_response_editing);

                return (
                  <button
                    key={option.id}
                    type="button"
                    disabled={!canSelect}
                    onClick={() => setSelectedOptionId(option.id)}
                    className={`w-full text-left p-4 rounded-2xl border-2 transition-all flex items-center justify-between ${
                      isSelected
                        ? 'border-indigo-600 bg-indigo-50/50 shadow-sm shadow-indigo-100'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    } ${!canSelect ? 'cursor-default opacity-85' : 'cursor-pointer active:scale-98'}`}
                  >
                    <span className={`text-base font-semibold ${isSelected ? 'text-indigo-900' : 'text-slate-800'}`}>
                      {option.option_text}
                    </span>

                    <div
                      className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                        isSelected ? 'border-indigo-600 bg-indigo-600' : 'border-slate-300 bg-white'
                      }`}
                    >
                      {isSelected && <div className="w-2.5 h-2.5 rounded-full bg-white" />}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Action Button */}
            {!isExpired && (!poll.has_responded || poll.allow_response_editing) && (
              <button
                type="submit"
                disabled={respondMutation.isPending || !currentSelection}
                className="w-full py-3.5 px-4 rounded-2xl text-base font-bold text-white bg-indigo-600 hover:bg-indigo-700 shadow-lg shadow-indigo-200 active:scale-98 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {respondMutation.isPending ? (
                  <span>Saving response...</span>
                ) : (
                  <>
                    <Vote className="w-5 h-5" />
                    <span>{poll.has_responded ? 'Update Response' : 'Submit Response'}</span>
                  </>
                )}
              </button>
            )}

            <div className="pt-2 text-center">
              <Link
                to="/student/dashboard"
                className="text-xs font-semibold text-slate-500 hover:text-slate-700 transition-colors"
              >
                ← Back to Student Dashboard
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
