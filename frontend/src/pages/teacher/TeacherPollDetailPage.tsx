import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Vote,
  CheckCircle2,
  XCircle,
  Clock,
  MessageSquareShare,
  Search,
  Filter,
  ArrowUpDown,
  Share2,
  Lock,
  ArrowRight,
  School,
  AlertCircle,
  Send,
  Bell,
  RefreshCw,
  Phone,
  CheckSquare,
  Square,
  MessageCircle,
  Info,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts';
import api from '../../api/client';
import { PollParticipantsResponse, MessageLogItem, ReminderResponse } from '../../types';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';
import { Badge } from '../../components/common/Badge';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { WhatsAppShareModal } from '../../components/common/WhatsAppShareModal';

export const TeacherPollDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const pollId = Number(id);
  const { user } = useAuth();
  const isRep = user?.role === 'STUDENT';
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState<'ALL' | 'DONE' | 'NOT_DONE'>('ALL');
  const [sortBy, setSortBy] = useState<'NAME' | 'REG_NO' | 'TIME'>('REG_NO');
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);

  // WhatsApp Reminder Modal State
  const [isRemindModalOpen, setIsRemindModalOpen] = useState(false);
  const [targetStudentIds, setTargetStudentIds] = useState<number[]>([]);
  const [selectedStudentIds, setSelectedStudentIds] = useState<number[]>([]);
  const [customMessage, setCustomMessage] = useState('');
  const [isLogsExpanded, setIsLogsExpanded] = useState(true);

  // Poll participant data
  const { data, isLoading } = useQuery<PollParticipantsResponse>({
    queryKey: ['poll-participants', pollId],
    queryFn: async () => {
      const res = await api.get(`/polls/${pollId}/participants`);
      return res.data;
    },
    enabled: Boolean(pollId),
    refetchInterval: 5000, // Live updates every 5 seconds!
  });

  // Message Logs data
  const { data: messageLogs, isLoading: logsLoading, refetch: refetchLogs } = useQuery<MessageLogItem[]>({
    queryKey: ['poll-messages', pollId],
    queryFn: async () => {
      const res = await api.get(`/polls/${pollId}/messages`);
      return res.data;
    },
    enabled: Boolean(pollId),
  });

  // Send WhatsApp Reminders Mutation
  const remindMutation = useMutation({
    mutationFn: async (payload: { student_ids?: number[]; custom_message?: string }) => {
      const res = await api.post(`/polls/${pollId}/remind`, payload);
      return res.data as ReminderResponse;
    },
    onSuccess: (resData) => {
      queryClient.invalidateQueries({ queryKey: ['poll-participants', pollId] });
      queryClient.invalidateQueries({ queryKey: ['poll-messages', pollId] });
      setIsRemindModalOpen(false);
      setSelectedStudentIds([]);
      setCustomMessage('');

      if (resData.whatsapp_configured === false) {
        toastError('WhatsApp integration is not configured. Please set WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID in backend.');
      } else if (resData.sent_count > 0 && resData.failed_count === 0) {
        success(`Message submitted successfully (${resData.sent_count} reminder${resData.sent_count > 1 ? 's' : ''} dispatched).`);
      } else if (resData.sent_count > 0 && resData.failed_count > 0) {
        success(`Dispatched ${resData.sent_count} reminder(s), but ${resData.failed_count} failed. See delivery logs.`);
      } else if (resData.sent_count === 0 && resData.total_targeted > 0) {
        const firstErr = resData.results?.[0]?.error_message || 'Message failed to send.';
        toastError(`Failed to send reminder: ${firstErr}`);
      } else {
        success('No pending non-responders targeted.');
      }
    },
    onError: (err: any) => {
      toastError(err.response?.data?.detail || 'Failed to dispatch WhatsApp reminders.');
    },
  });

  // Close Poll mutation
  const closePollMutation = useMutation({
    mutationFn: async () => {
      const res = await api.patch(`/polls/${pollId}`, { status: 'CLOSED' });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['poll-participants', pollId] });
      success('Poll closed. Submissions are now locked.');
    },
    onError: () => toastError('Failed to close poll.'),
  });

  if (isLoading) {
    return <LoadingSpinner message="Fetching live participation data..." />;
  }

  if (!data) {
    return <div>Poll not found</div>;
  }

  // Combine and filter participants
  const allParticipants = [
    ...data.done_students.map((s) => ({ ...s, is_done: true })),
    ...data.not_done_students.map((s) => ({ ...s, is_done: false })),
  ];

  const filtered = allParticipants
    .filter((p) => {
      if (filterStatus === 'DONE') return p.is_done;
      if (filterStatus === 'NOT_DONE') return !p.is_done;
      return true;
    })
    .filter((p) => {
      const query = search.toLowerCase();
      return (
        p.name.toLowerCase().includes(query) ||
        (p.register_number && p.register_number.toLowerCase().includes(query)) ||
        (p.option_text && p.option_text.toLowerCase().includes(query))
      );
    })
    .sort((a, b) => {
      if (sortBy === 'NAME') return a.name.localeCompare(b.name);
      if (sortBy === 'REG_NO') return (a.register_number || '').localeCompare(b.register_number || '');
      if (sortBy === 'TIME') {
        const tA = a.submitted_at ? new Date(a.submitted_at).getTime() : 0;
        const tB = b.submitted_at ? new Date(b.submitted_at).getTime() : 0;
        return tB - tA;
      }
      return 0;
    });

  const frontendBase = window.location.origin;
  const shareUrl = `${frontendBase}/poll/${data.public_id}`;
  const whatsappText = `*${data.class_name} Poll*\n\n${data.question}\n\n👉 Submit your response here:\n${shareUrl}`;
  const whatsappShareUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(whatsappText)}`;

  const chartColors = ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div>
        <div className="flex items-center gap-2 text-xs text-slate-500 mb-2">
          <Link to={isRep ? "/rep/classes" : "/teacher/classes"} className="hover:text-slate-800">
            {isRep ? "Assigned Classes" : "Classes"}
          </Link>
          <span>/</span>
          <Link to={isRep ? `/rep/classes/${data.class_id}` : `/teacher/classes/${data.class_id}`} className="hover:text-slate-800">
            {data.class_name}
          </Link>
          <span>/</span>
          <span className="font-semibold text-slate-800">Poll Results</span>
        </div>

        <div className="p-6 md:p-8 rounded-3xl bg-white border border-slate-100 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700">
                {data.class_name}
              </span>
              <Badge variant={data.is_closed ? 'closed' : 'active'}>
                {data.is_closed ? 'CLOSED' : 'LIVE ACTIVE'}
              </Badge>
              {isRep && <Badge variant="rep">REP ACCESS</Badge>}
            </div>
            <h1 className="text-2xl font-black text-slate-900 leading-snug">{data.question}</h1>
            <p className="text-xs text-slate-500 mt-1 flex items-center gap-2">
              <Clock className="w-3.5 h-3.5" />
              <span>
                Deadline: {new Date(data.deadline).toLocaleDateString([], { month: 'short', day: 'numeric' })}{' '}
                {new Date(data.deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0 flex-wrap">
            <button
              onClick={() => setIsShareModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-xl shadow-xs transition-all active:scale-95"
            >
              <MessageSquareShare className="w-4 h-4" />
              <span>Share Link</span>
            </button>

            {!data.is_closed && data.pending_count > 0 && (
              <button
                onClick={() => {
                  setTargetStudentIds([]);
                  setIsRemindModalOpen(true);
                }}
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl shadow-xs transition-all active:scale-95"
              >
                <Send className="w-4 h-4" />
                <span>Remind Non-Responders ({data.pending_count})</span>
              </button>
            )}

            {!data.is_closed && (user?.role === 'FACULTY' || user?.role === 'TEACHER' || data.creator_id === user?.id) && (
              <button
                onClick={() => closePollMutation.mutate()}
                disabled={closePollMutation.isPending}
                className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-semibold rounded-xl transition-colors"
              >
                Close Poll
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Primary KPI Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
            Total Students
          </span>
          <p className="text-3xl font-black text-slate-900">{data.total_students}</p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider block">DONE</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-3xl font-black text-emerald-600">{data.completed_count}</p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-rose-600 uppercase tracking-wider block">NOT DONE</span>
            <XCircle className="w-4 h-4 text-rose-600" />
          </div>
          <p className="text-3xl font-black text-rose-600">{data.pending_count}</p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs">
          <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider block mb-1">
            Completion Rate
          </span>
          <p className="text-3xl font-black text-indigo-600">{data.completion_rate}%</p>
        </div>
      </div>

      {/* Results Chart Section */}
      <div className="p-6 md:p-8 rounded-3xl bg-white border border-slate-100 shadow-xs">
        <h3 className="text-base font-bold text-slate-900 mb-6">Vote Distribution Breakdown</h3>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          {/* Recharts Bar Chart */}
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.options} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                <XAxis dataKey="option_text" stroke="#64748b" fontSize={12} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} allowDecimals={false} />
                <Tooltip
                  formatter={(val: any) => [`${val} votes`, 'Count']}
                  contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0' }}
                />
                <Bar dataKey="votes_count" radius={[8, 8, 0, 0]}>
                  {data.options.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={chartColors[index % chartColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Option Cards */}
          <div className="space-y-3">
            {data.options.map((opt, idx) => (
              <div
                key={opt.id}
                className="p-4 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-3.5 h-3.5 rounded-full shrink-0"
                    style={{ backgroundColor: chartColors[idx % chartColors.length] }}
                  />
                  <span className="font-bold text-slate-800 text-sm">{opt.option_text}</span>
                </div>
                <div className="text-right">
                  <span className="font-black text-slate-900 text-sm">{opt.votes_count} votes</span>
                  <span className="text-xs text-slate-500 block">{opt.percentage}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Interactive DONE / NOT DONE Student List */}
      <div className="bg-white rounded-3xl border border-slate-100 shadow-xs overflow-hidden">
        {/* Controls toolbar */}
        <div className="p-6 border-b border-slate-100 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 bg-slate-50/50">
          <div>
            <h3 className="text-base font-bold text-slate-900">Student Participation Roster</h3>
            <p className="text-xs text-slate-500">Live system of record: who has answered and who is pending.</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search */}
            <div className="relative min-w-[200px]">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search name or reg no..."
                className="w-full pl-9 pr-3 py-2 bg-white border border-slate-200 rounded-xl text-xs focus:outline-hidden focus:border-indigo-600"
              />
            </div>

            {/* Filter pills */}
            <div className="flex rounded-xl bg-slate-200/70 p-1 text-xs font-semibold">
              <button
                onClick={() => setFilterStatus('ALL')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  filterStatus === 'ALL' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
                }`}
              >
                All ({allParticipants.length})
              </button>
              <button
                onClick={() => setFilterStatus('DONE')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  filterStatus === 'DONE' ? 'bg-emerald-600 text-white shadow-xs' : 'text-slate-600'
                }`}
              >
                DONE ({data.completed_count})
              </button>
              <button
                onClick={() => setFilterStatus('NOT_DONE')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  filterStatus === 'NOT_DONE' ? 'bg-rose-600 text-white shadow-xs' : 'text-slate-600'
                }`}
              >
                NOT DONE ({data.pending_count})
              </button>
            </div>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs text-slate-700 focus:outline-hidden"
            >
              <option value="REG_NO">Sort by Reg. Number</option>
              <option value="NAME">Sort by Name</option>
              <option value="TIME">Sort by Submission Time</option>
            </select>
          </div>
        </div>

        {/* Selected Action Banner */}
        {selectedStudentIds.length > 0 && !data.is_closed && (
          <div className="px-6 py-3 bg-indigo-50 border-b border-indigo-100 flex items-center justify-between animate-in fade-in">
            <span className="text-xs font-bold text-indigo-900">
              {selectedStudentIds.length} pending student{selectedStudentIds.length > 1 ? 's' : ''} selected for reminder
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setSelectedStudentIds([])}
                className="px-3 py-1 text-xs font-semibold text-slate-600 hover:text-slate-800"
              >
                Deselect All
              </button>
              <button
                onClick={() => {
                  setTargetStudentIds(selectedStudentIds);
                  setIsRemindModalOpen(true);
                }}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-all active:scale-95"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Send WhatsApp Reminder to Selected ({selectedStudentIds.length})</span>
              </button>
            </div>
          </div>
        )}

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-100">
              <tr>
                {!data.is_closed && (
                  <th className="px-4 py-3.5 w-10 text-center">
                    <input
                      type="checkbox"
                      checked={
                        filtered.some((p) => !p.is_done) &&
                        filtered
                          .filter((p) => !p.is_done)
                          .every((p) => selectedStudentIds.includes(p.student_id))
                      }
                      onChange={(e) => {
                        const pendings = filtered.filter((p) => !p.is_done).map((p) => p.student_id);
                        if (e.target.checked) {
                          setSelectedStudentIds(Array.from(new Set([...selectedStudentIds, ...pendings])));
                        } else {
                          const removeSet = new Set(pendings);
                          setSelectedStudentIds(selectedStudentIds.filter((id) => !removeSet.has(id)));
                        }
                      }}
                      className="w-4 h-4 rounded text-indigo-600 border-slate-300 cursor-pointer"
                      title="Select all pending non-responders in view"
                    />
                  </th>
                )}
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Student Name</th>
                <th className="px-6 py-3.5">Register Number</th>
                <th className="px-6 py-3.5">WhatsApp Mobile</th>
                <th className="px-6 py-3.5">Selected Response</th>
                <th className="px-6 py-3.5">Submission Time</th>
                {!data.is_closed && <th className="px-6 py-3.5 text-right">Action</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((student) => {
                const isSelected = selectedStudentIds.includes(student.student_id);
                return (
                  <tr
                    key={student.student_id}
                    className={`hover:bg-slate-50/70 transition-colors ${
                      student.is_done ? '' : isSelected ? 'bg-indigo-50/40' : 'bg-rose-50/20'
                    }`}
                  >
                    {!data.is_closed && (
                      <td className="px-4 py-4 text-center">
                        {!student.is_done ? (
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedStudentIds([...selectedStudentIds, student.student_id]);
                              } else {
                                setSelectedStudentIds(
                                  selectedStudentIds.filter((id) => id !== student.student_id)
                                );
                              }
                            }}
                            className="w-4 h-4 rounded text-indigo-600 border-slate-300 cursor-pointer"
                          />
                        ) : (
                          <span className="text-slate-300">—</span>
                        )}
                      </td>
                    )}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant={student.is_done ? 'done' : 'not-done'}>
                        {student.is_done ? '✓ DONE' : '✗ NOT DONE'}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-900 whitespace-nowrap">
                      {student.name}
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-600 whitespace-nowrap">
                      {student.register_number || '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs">
                      {student.phone_number ? (
                        <span className="font-mono text-slate-700">{student.phone_number}</span>
                      ) : (
                        <span className="text-slate-400 italic">No phone</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {student.option_text ? (
                        <span className="px-3 py-1 rounded-lg bg-indigo-50 text-indigo-700 text-xs font-bold">
                          {student.option_text}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400 italic">Pending response</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-500">
                      {student.submitted_at ? (
                        new Date(student.submitted_at).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit',
                        })
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    {!data.is_closed && (
                      <td className="px-6 py-4 whitespace-nowrap text-right text-xs">
                        {!student.is_done && (
                          <button
                            onClick={() => {
                              setTargetStudentIds([student.student_id]);
                              setIsRemindModalOpen(true);
                            }}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 rounded-lg transition-colors"
                            title="Send individual WhatsApp reminder"
                          >
                            <Send className="w-3.5 h-3.5" />
                            <span>Remind</span>
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* WHATSAPP DELIVERY LOGS SECTION */}
      <div className="bg-white rounded-3xl border border-slate-100 shadow-xs overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-50/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
              <MessageCircle className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900">
                  WhatsApp Cloud API Delivery Logs
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                  {messageLogs?.length || 0} Logged
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Audit trail of official Meta WhatsApp Business Cloud API reminders.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => refetchLogs()}
              disabled={logsLoading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 hover:bg-slate-50 rounded-xl text-xs font-semibold text-slate-700 transition-colors shadow-2xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${logsLoading ? 'animate-spin' : ''}`} />
              <span>Refresh Logs</span>
            </button>
            <button
              onClick={() => setIsLogsExpanded(!isLogsExpanded)}
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 px-2 py-1"
            >
              {isLogsExpanded ? 'Hide' : 'Show'}
            </button>
          </div>
        </div>

        {isLogsExpanded && (
          <div className="overflow-x-auto">
            {logsLoading ? (
              <div className="p-8 text-center text-xs text-slate-400">Loading delivery logs...</div>
            ) : !messageLogs || messageLogs.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                No WhatsApp reminders have been dispatched for this poll yet.
              </div>
            ) : (
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-100">
                  <tr>
                    <th className="px-6 py-3">Student</th>
                    <th className="px-6 py-3">Register No</th>
                    <th className="px-6 py-3">Recipient Phone</th>
                    <th className="px-6 py-3">Provider</th>
                    <th className="px-6 py-3">Delivery Status</th>
                    <th className="px-6 py-3">Sent Time</th>
                    <th className="px-6 py-3">Reference / Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {messageLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="px-6 py-3.5 font-semibold text-slate-900">{log.student_name}</td>
                      <td className="px-6 py-3.5 font-mono text-slate-600">{log.student_register_number || '—'}</td>
                      <td className="px-6 py-3.5 font-mono text-slate-600">{log.recipient_phone}</td>
                      <td className="px-6 py-3.5">
                        <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium">
                          {log.provider}
                        </span>
                      </td>
                      <td className="px-6 py-3.5">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase ${
                            log.delivery_status === 'DELIVERED' || log.delivery_status === 'READ'
                              ? 'bg-emerald-100 text-emerald-800'
                              : log.delivery_status === 'SENT'
                              ? 'bg-sky-100 text-sky-800'
                              : log.delivery_status === 'PENDING'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-rose-100 text-rose-800'
                          }`}
                        >
                          {log.delivery_status}
                        </span>
                      </td>
                      <td className="px-6 py-3.5 text-slate-500 whitespace-nowrap">
                        {new Date(log.sent_at).toLocaleString([], {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </td>
                      <td className="px-6 py-3.5 text-[11px] max-w-xs">
                        {log.delivery_status === 'FAILED' ? (
                          <span
                            className="font-sans text-rose-600 font-medium line-clamp-2 block"
                            title={log.error_message || undefined}
                          >
                            {log.error_message || 'Delivery rejected by provider'}
                          </span>
                        ) : (
                          <span
                            className="font-mono text-slate-500 truncate block max-w-[200px]"
                            title={log.provider_message_id || 'Submitted'}
                          >
                            {log.provider_message_id || 'Submitted to Meta'}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>

      {/* WHATSAPP REMINDER CONFIRMATION MODAL */}
      {isRemindModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 md:p-8 shadow-2xl border border-slate-100 space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-indigo-100 text-indigo-700 flex items-center justify-center">
                  <Bell className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-900">Send WhatsApp Reminder</h2>
                  <p className="text-xs text-slate-500">Official WhatsApp Cloud API Direct Dispatch</p>
                </div>
              </div>
              <button
                onClick={() => setIsRemindModalOpen(false)}
                className="p-2 text-slate-400 hover:text-slate-600 rounded-xl hover:bg-slate-100 transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Target Audience Summary */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">Target Recipients</span>
                <span className="font-bold text-slate-900">
                  {targetStudentIds.length > 0 ? targetStudentIds.length : data.pending_count} pending students
                </span>
              </div>
              <div className="text-xs text-slate-600 font-medium">
                {targetStudentIds.length > 0 ? (
                  <span>
                    Selected:{' '}
                    {allParticipants
                      .filter((p) => targetStudentIds.includes(p.student_id))
                      .map((p) => p.name)
                      .slice(0, 4)
                      .join(', ')}
                    {targetStudentIds.length > 4 ? ` and ${targetStudentIds.length - 4} more` : ''}
                  </span>
                ) : (
                  <span>All students who have not yet submitted a response for this poll.</span>
                )}
              </div>
            </div>

            {/* Official Message Template Preview */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Template Preview (WhatsApp Cloud API)
                </span>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700">
                  Official Meta Graph API
                </span>
              </div>
              <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200/60 text-xs text-emerald-950 font-sans space-y-2">
                <p className="font-semibold">Hello {'{{student_name}}'},</p>
                <p>
                  You have a pending poll from <span className="font-bold">{data.class_name}</span>:
                </p>
                <p className="italic bg-white/70 p-2 rounded-xl border border-emerald-200/50">
                  "{data.question}"
                </p>
                <p>
                  Deadline:{' '}
                  {new Date(data.deadline).toLocaleString([], {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
                <p className="text-emerald-700 underline break-all">{shareUrl}</p>
                {customMessage.trim() && (
                  <p className="pt-2 border-t border-emerald-200 text-indigo-900 font-medium">
                    Note: "{customMessage.trim()}"
                  </p>
                )}
              </div>
            </div>

            {/* Optional Note */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Optional Message Note (Included in notification)
              </label>
              <input
                type="text"
                value={customMessage}
                onChange={(e) => setCustomMessage(e.target.value)}
                placeholder="e.g. Please submit before 4 PM today for the attendance record."
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
              />
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsRemindModalOpen(false)}
                className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-xl"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() =>
                  remindMutation.mutate({
                    student_ids: targetStudentIds.length > 0 ? targetStudentIds : undefined,
                    custom_message: customMessage || undefined,
                  })
                }
                disabled={remindMutation.isPending}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl shadow-md shadow-indigo-100 transition-all active:scale-95 disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
                <span>
                  {remindMutation.isPending
                    ? 'Dispatching...'
                    : `Confirm & Send (${targetStudentIds.length > 0 ? targetStudentIds.length : data.pending_count})`}
                </span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* WhatsApp Share Modal */}
      <WhatsAppShareModal
        isOpen={isShareModalOpen}
        onClose={() => setIsShareModalOpen(false)}
        classNameTitle={data.class_name}
        question={data.question}
        shareUrl={shareUrl}
        whatsappShareUrl={whatsappShareUrl}
      />
    </div>
  );
};
