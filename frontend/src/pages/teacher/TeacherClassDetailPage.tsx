import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  BookOpen,
  Users,
  Vote,
  ShieldCheck,
  Settings,
  Plus,
  Share2,
  Clock,
  CheckCircle2,
  Trash2,
  Search,
  ArrowRight,
  ExternalLink,
  MessageSquareShare,
  UserPlus,
  Volume2,
  VolumeX,
  UserX,
  Phone,
  Check,
} from 'lucide-react';
import api from '../../api/client';
import { ClassItem, Poll, ClassMember, StudentSearchItem } from '../../types';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';
import { Badge } from '../../components/common/Badge';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';
import { WhatsAppShareModal } from '../../components/common/WhatsAppShareModal';

export const TeacherClassDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const classId = Number(id);
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [activeTab, setActiveTab] = useState<'polls' | 'students' | 'reps' | 'settings'>('polls');
  const [isCreatePollOpen, setIsCreatePollOpen] = useState(false);
  const [isAddStudentOpen, setIsAddStudentOpen] = useState(false);
  const [searchStudent, setSearchStudent] = useState('');
  const [studentDirectoryQuery, setStudentDirectoryQuery] = useState('');
  const [manualRegNo, setManualRegNo] = useState('');

  // WhatsApp Share Modal state
  const [shareModalData, setShareModalData] = useState<{
    isOpen: boolean;
    classNameTitle: string;
    question: string;
    shareUrl: string;
    whatsappShareUrl: string;
  }>({
    isOpen: false,
    classNameTitle: '',
    question: '',
    shareUrl: '',
    whatsappShareUrl: '',
  });

  // Create Poll Form State
  const [pollForm, setPollForm] = useState({
    question: '',
    options: ['Yes', 'No'],
    deadlineDate: '',
    deadlineTime: '23:59',
    allow_response_editing: true,
  });

  // 1. Class details
  const { data: classData, isLoading: classLoading } = useQuery<ClassItem>({
    queryKey: ['class-detail', classId],
    queryFn: async () => {
      const res = await api.get(`/classes/${classId}`);
      return res.data;
    },
    enabled: Boolean(classId),
  });

  const isRep = user?.role === 'STUDENT' || Boolean(classData?.is_rep);

  // 2. Class Polls
  const { data: polls, isLoading: pollsLoading } = useQuery<Poll[]>({
    queryKey: ['class-polls', classId],
    queryFn: async () => {
      const res = await api.get(`/classes/${classId}/polls`);
      return res.data;
    },
    enabled: Boolean(classId),
  });

  // 3. Class Students
  const { data: students, isLoading: studentsLoading } = useQuery<ClassMember[]>({
    queryKey: ['class-students', classId],
    queryFn: async () => {
      const res = await api.get(`/classes/${classId}/students`);
      return res.data;
    },
    enabled: Boolean(classId),
  });

  // Poll Creation Mutation
  const createPollMutation = useMutation({
    mutationFn: async () => {
      if (!pollForm.deadlineDate) {
        throw new Error('Please select a deadline date');
      }
      const deadlineIso = new Date(`${pollForm.deadlineDate}T${pollForm.deadlineTime}:00Z`).toISOString();
      const res = await api.post(`/classes/${classId}/polls`, {
        question: pollForm.question,
        options: pollForm.options.filter((o) => o.trim().length > 0),
        deadline: deadlineIso,
        allow_response_editing: pollForm.allow_response_editing,
      });
      return res.data;
    },
    onSuccess: (newPoll: Poll) => {
      queryClient.invalidateQueries({ queryKey: ['class-polls', classId] });
      queryClient.invalidateQueries({ queryKey: ['teacher-dashboard-stats'] });
      setIsCreatePollOpen(false);
      setPollForm({
        question: '',
        options: ['Yes', 'No'],
        deadlineDate: '',
        deadlineTime: '23:59',
        allow_response_editing: true,
      });
      success('Poll created successfully!');

      // Automatically open WhatsApp Share Modal
      setShareModalData({
        isOpen: true,
        classNameTitle: newPoll.class_name,
        question: newPoll.question,
        shareUrl: newPoll.share_url,
        whatsappShareUrl: newPoll.whatsapp_share_url,
      });
    },
    onError: (err: any) => {
      toastError(err.response?.data?.detail || err.message || 'Failed to create poll.');
    },
  });

  // Assign REP Mutation
  const assignRepMutation = useMutation({
    mutationFn: async (studentId: number) => {
      const res = await api.post(`/classes/${classId}/reps`, { student_id: studentId });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['class-students', classId] });
      queryClient.invalidateQueries({ queryKey: ['class-detail', classId] });
      success('Student assigned as Class Representative!');
    },
    onError: (err: any) => {
      toastError(err.response?.data?.detail || 'Failed to assign REP.');
    },
  });

  // Remove REP Mutation
  const removeRepMutation = useMutation({
    mutationFn: async (studentId: number) => {
      const res = await api.delete(`/classes/${classId}/reps/${studentId}`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['class-students', classId] });
      queryClient.invalidateQueries({ queryKey: ['class-detail', classId] });
      success('Representative assignment removed.');
    },
    onError: (err: any) => {
      toastError(err.response?.data?.detail || 'Failed to remove REP.');
    },
  });

  // Toggle REP Poll Creation Mutation
  const toggleRepPollMutation = useMutation({
    mutationFn: async (enabled: boolean) => {
      const res = await api.patch(`/classes/${classId}`, { allow_rep_poll_creation: enabled });
      return res.data;
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(['class-detail', classId], updated);
      success(`REP poll creation ${updated.allow_rep_poll_creation ? 'enabled' : 'disabled'}.`);
    },
  });

  // Search Students in Institutional Directory
  const { data: searchResults, isLoading: isSearchingDirectory } = useQuery<StudentSearchItem[]>({
    queryKey: ['students-search', studentDirectoryQuery],
    queryFn: async () => {
      if (!studentDirectoryQuery.trim()) return [];
      const res = await api.get(`/students/search?q=${encodeURIComponent(studentDirectoryQuery.trim())}`);
      return res.data;
    },
    enabled: studentDirectoryQuery.trim().length >= 2,
  });

  // Add Student to Class Mutation
  const addStudentMutation = useMutation({
    mutationFn: async (payload: { student_id?: number; register_number?: string }) => {
      const res = await api.post(`/classes/${classId}/students`, payload);
      return res.data;
    },
    onSuccess: (newMember: ClassMember) => {
      queryClient.invalidateQueries({ queryKey: ['class-students', classId] });
      queryClient.invalidateQueries({ queryKey: ['class-detail', classId] });
      queryClient.invalidateQueries({ queryKey: ['students-search', studentDirectoryQuery] });
      success(`${newMember.name} added to ${classData?.name || 'class'}!`);
      setManualRegNo('');
      setStudentDirectoryQuery('');
      setIsAddStudentOpen(false);
    },
    onError: (err: any) => {
      toastError(err.response?.data?.detail || 'Failed to add student to class.');
    },
  });

  // Remove Student from Class Mutation
  const removeStudentMutation = useMutation({
    mutationFn: async (studentId: number) => {
      const res = await api.delete(`/classes/${classId}/students/${studentId}`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['class-students', classId] });
      queryClient.invalidateQueries({ queryKey: ['class-detail', classId] });
      success('Student removed from class.');
    },
    onError: (err: any) => {
      toastError(err.response?.data?.detail || 'Failed to remove student.');
    },
  });

  // Mute / Unmute Student Mutation
  const muteStudentMutation = useMutation({
    mutationFn: async ({ studentId, isMuted }: { studentId: number; isMuted: boolean }) => {
      const res = await api.patch(`/classes/${classId}/members/${studentId}/mute`, { is_muted: isMuted });
      return res.data;
    },
    onSuccess: (resData) => {
      queryClient.invalidateQueries({ queryKey: ['class-students', classId] });
      success(resData.message || 'Student mute status updated.');
    },
    onError: (err: any) => {
      toastError(err.response?.data?.detail || 'Failed to update mute status.');
    },
  });

  if (classLoading) {
    return <LoadingSpinner message="Loading class workspace..." />;
  }

  if (!classData) {
    return <div>Class not found</div>;
  }

  const filteredStudents =
    students?.filter(
      (s) =>
        s.name.toLowerCase().includes(searchStudent.toLowerCase()) ||
        (s.register_number && s.register_number.toLowerCase().includes(searchStudent.toLowerCase()))
    ) || [];

  const repList = students?.filter((s) => s.is_rep) || [];

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Header */}
      <div>
        <div className="flex items-center gap-2 text-xs text-slate-500 mb-2">
          <Link to={isRep ? "/rep/classes" : "/teacher/classes"} className="hover:text-slate-800">
            {isRep ? "Assigned Classes" : "My Classes"}
          </Link>
          <span>/</span>
          <span className="font-semibold text-slate-800">{classData.name}</span>
        </div>

        <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-black text-slate-900">{classData.name}</h1>
              <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700">
                Code: {classData.class_code}
              </span>
              {isRep && <Badge variant="rep">REP ACCESS</Badge>}
            </div>
            <p className="text-sm text-slate-500 mt-1">
              {classData.department} • Year {classData.year} (Sec {classData.section}) • AY {classData.academic_year}
            </p>
          </div>

          <div className="flex items-center gap-2">
            {isRep && !classData.allow_rep_poll_creation ? (
              <div className="flex items-center gap-2 px-3.5 py-2 bg-amber-50 text-amber-800 border border-amber-200/80 rounded-xl text-xs font-semibold">
                <ShieldCheck className="w-4 h-4 text-amber-600 shrink-0" />
                <span>REP Poll Creation Disabled by Faculty</span>
              </div>
            ) : (
              <button
                onClick={() => setIsCreatePollOpen(true)}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl shadow-md shadow-indigo-100 transition-all active:scale-95"
              >
                <Plus className="w-4 h-4" />
                <span>Create Poll</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-6 text-sm font-semibold text-slate-500">
        <button
          onClick={() => setActiveTab('polls')}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === 'polls' ? 'border-indigo-600 text-indigo-600' : 'border-transparent hover:text-slate-800'
          }`}
        >
          Class Polls ({polls?.length || 0})
        </button>

        <button
          onClick={() => setActiveTab('students')}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === 'students' ? 'border-indigo-600 text-indigo-600' : 'border-transparent hover:text-slate-800'
          }`}
        >
          Students ({students?.length || 0})
        </button>

        <button
          onClick={() => setActiveTab('reps')}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === 'reps' ? 'border-indigo-600 text-indigo-600' : 'border-transparent hover:text-slate-800'
          }`}
        >
          Representatives ({repList.length})
        </button>

        {!isRep && (
          <button
            onClick={() => setActiveTab('settings')}
            className={`pb-3 border-b-2 transition-colors ${
              activeTab === 'settings' ? 'border-indigo-600 text-indigo-600' : 'border-transparent hover:text-slate-800'
            }`}
          >
            Settings
          </button>
        )}
      </div>

      {/* TAB 1: POLLS */}
      {activeTab === 'polls' && (
        <div className="space-y-4">
          {pollsLoading ? (
            <LoadingSpinner message="Loading class polls..." />
          ) : !polls || polls.length === 0 ? (
            <EmptyState
              icon={Vote}
              title="No polls created yet"
              description="Create a poll with custom options and a deadline, then share it to your class WhatsApp group."
              action={{
                label: 'Create First Poll',
                onClick: () => setIsCreatePollOpen(true),
              }}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {polls.map((poll) => (
                <div
                  key={poll.id}
                  className="p-6 rounded-3xl bg-white border border-slate-100 shadow-xs hover:border-indigo-100 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <Badge variant={poll.is_closed ? 'closed' : 'active'}>
                        {poll.is_closed ? 'CLOSED' : 'ACTIVE'}
                      </Badge>
                      <span className="text-xs text-slate-400">
                        {new Date(poll.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    <h3 className="text-lg font-bold text-slate-900 leading-snug">{poll.question}</h3>

                    <div className="mt-4 p-3.5 rounded-2xl bg-slate-50 border border-slate-100 grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-slate-500 block">Responses</span>
                        <span className="font-bold text-slate-800 text-sm">
                          {poll.total_responses} / {poll.total_students}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">Completion</span>
                        <span className="font-bold text-emerald-600 text-sm">{poll.completion_rate}%</span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between gap-2">
                    <button
                      onClick={() =>
                        setShareModalData({
                          isOpen: true,
                          classNameTitle: poll.class_name,
                          question: poll.question,
                          shareUrl: poll.share_url,
                          whatsappShareUrl: poll.whatsapp_share_url,
                        })
                      }
                      className="inline-flex items-center gap-1.5 px-3 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-xs font-semibold rounded-xl transition-colors"
                    >
                      <MessageSquareShare className="w-3.5 h-3.5" />
                      <span>WhatsApp Link</span>
                    </button>

                    <Link
                      to={isRep ? `/rep/polls/${poll.id}` : `/teacher/polls/${poll.id}`}
                      className="inline-flex items-center gap-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-all active:scale-95"
                    >
                      <span>Live Done/Not Done</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: STUDENTS ROSTER */}
      {activeTab === 'students' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
            <div className="relative max-w-sm w-full">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchStudent}
                onChange={(e) => setSearchStudent(e.target.value)}
                placeholder="Search enrolled students..."
                className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-xs focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
              />
            </div>

            {!isRep && (
              <button
                onClick={() => setIsAddStudentOpen(true)}
                className="inline-flex items-center justify-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-all active:scale-95"
              >
                <UserPlus className="w-4 h-4" />
                <span>Add Student to Class</span>
              </button>
            )}
          </div>

          <div className="bg-white rounded-2xl border border-slate-100 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-100">
                  <tr>
                    <th className="px-6 py-3.5">Student Name</th>
                    <th className="px-6 py-3.5">Register Number</th>
                    <th className="px-6 py-3.5">Mobile / WhatsApp</th>
                    <th className="px-6 py-3.5">Email</th>
                    <th className="px-6 py-3.5">Role & Status</th>
                    {!isRep && <th className="px-6 py-3.5 text-right">Actions</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredStudents.length === 0 ? (
                    <tr>
                      <td colSpan={isRep ? 5 : 6} className="px-6 py-8 text-center text-xs text-slate-400">
                        No students found matching your filter.
                      </td>
                    </tr>
                  ) : (
                    filteredStudents.map((s) => (
                      <tr key={s.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="px-6 py-3.5 font-semibold text-slate-900">{s.name}</td>
                        <td className="px-6 py-3.5 font-mono text-xs text-slate-600">{s.register_number || '—'}</td>
                        <td className="px-6 py-3.5 text-xs">
                          {s.phone_number ? (
                            <span className="font-mono text-slate-700">{s.phone_number}</span>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                        <td className="px-6 py-3.5 text-xs text-slate-500">{s.email}</td>
                        <td className="px-6 py-3.5">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            {s.is_rep ? <Badge variant="rep">REP</Badge> : <Badge variant="student">Student</Badge>}
                            {s.is_muted && (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                                MUTED
                              </span>
                            )}
                          </div>
                        </td>
                        {!isRep && (
                          <td className="px-6 py-3.5 text-right">
                            <div className="flex items-center justify-end gap-2">
                              {/* Mute / Unmute Button */}
                              <button
                                onClick={() => muteStudentMutation.mutate({ studentId: s.user_id, isMuted: !s.is_muted })}
                                disabled={muteStudentMutation.isPending}
                                className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-lg transition-colors ${
                                  s.is_muted
                                    ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                                    : 'bg-amber-50 text-amber-800 hover:bg-amber-100'
                                }`}
                                title={s.is_muted ? 'Unmute student to allow responses' : 'Mute student to block responses'}
                              >
                                {s.is_muted ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
                                <span>{s.is_muted ? 'Unmute' : 'Mute'}</span>
                              </button>

                              {/* REP Toggle Button */}
                              {s.is_rep ? (
                                <button
                                  onClick={() => removeRepMutation.mutate(s.user_id)}
                                  disabled={removeRepMutation.isPending}
                                  className="px-2.5 py-1 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                                >
                                  Revoke REP
                                </button>
                              ) : (
                                <button
                                  onClick={() => assignRepMutation.mutate(s.user_id)}
                                  disabled={assignRepMutation.isPending}
                                  className="px-2.5 py-1 text-xs font-semibold text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                                >
                                  Make REP
                                </button>
                              )}

                              {/* Remove Student from Class */}
                              <button
                                onClick={() => {
                                  if (window.confirm(`Are you sure you want to remove ${s.name} from this class?`)) {
                                    removeStudentMutation.mutate(s.user_id);
                                  }
                                }}
                                disabled={removeStudentMutation.isPending}
                                className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                                title="Remove student from class"
                              >
                                <UserX className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        )}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: REPRESENTATIVES */}
      {activeTab === 'reps' && (
        <div className="space-y-4">
          {repList.length === 0 ? (
            <EmptyState
              icon={ShieldCheck}
              title="No Representatives assigned"
              description="Go to the Students tab to designate class representatives for this class."
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {repList.map((rep) => (
                <div
                  key={rep.id}
                  className="p-5 rounded-2xl bg-white border border-slate-100 shadow-xs flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center font-bold text-sm">
                      {rep.name.charAt(0)}
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-900 text-sm">{rep.name}</h4>
                      <p className="text-xs text-slate-500">
                        {rep.register_number} • {rep.email}
                      </p>
                    </div>
                  </div>
                  {!isRep && (
                    <button
                      onClick={() => removeRepMutation.mutate(rep.user_id)}
                      className="px-3 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                    >
                      Remove REP
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 4: SETTINGS */}
      {activeTab === 'settings' && (
        <div className="max-w-2xl bg-white rounded-3xl p-6 border border-slate-100 shadow-xs space-y-6">
          <div>
            <h3 className="text-base font-bold text-slate-900">Class Permission Settings</h3>
            <p className="text-xs text-slate-500 mt-0.5">Control feature capabilities for this class group.</p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between">
            <div>
              <span className="text-sm font-semibold text-slate-900 block">Allow REP to Create Polls</span>
              <p className="text-xs text-slate-500 mt-0.5">
                If enabled, assigned Class Representatives can post questions to this class.
              </p>
            </div>
            <button
              onClick={() => toggleRepPollMutation.mutate(!classData.allow_rep_poll_creation)}
              className={`w-12 h-6 rounded-full transition-colors relative ${
                classData.allow_rep_poll_creation ? 'bg-indigo-600' : 'bg-slate-300'
              }`}
            >
              <div
                className={`w-5 h-5 rounded-full bg-white transition-transform absolute top-0.5 ${
                  classData.allow_rep_poll_creation ? 'right-0.5' : 'left-0.5'
                }`}
              />
            </button>
          </div>
        </div>
      )}

      {/* CREATE POLL MODAL */}
      {isCreatePollOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 md:p-8 shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-slate-900 mb-1">Create Class Poll</h2>
            <p className="text-xs text-slate-500 mb-6">
              Post a question for {classData.name}. You will get a shareable WhatsApp link immediately.
            </p>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                createPollMutation.mutate();
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Poll Question
                </label>
                <textarea
                  required
                  rows={3}
                  value={pollForm.question}
                  onChange={(e) => setPollForm({ ...pollForm, question: e.target.value })}
                  placeholder="e.g. Will you attend tomorrow's industrial visit?"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                />
              </div>

              {/* Dynamic Options */}
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Options (Minimum 2)
                </label>
                {pollForm.options.map((opt, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <input
                      type="text"
                      required
                      value={opt}
                      onChange={(e) => {
                        const newOpts = [...pollForm.options];
                        newOpts[idx] = e.target.value;
                        setPollForm({ ...pollForm, options: newOpts });
                      }}
                      placeholder={`Option ${idx + 1}`}
                      className="flex-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                    />
                    {pollForm.options.length > 2 && (
                      <button
                        type="button"
                        onClick={() => {
                          const newOpts = pollForm.options.filter((_, i) => i !== idx);
                          setPollForm({ ...pollForm, options: newOpts });
                        }}
                        className="p-2 text-rose-500 hover:bg-rose-50 rounded-lg"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
                {pollForm.options.length < 6 && (
                  <button
                    type="button"
                    onClick={() => setPollForm({ ...pollForm, options: [...pollForm.options, ''] })}
                    className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1 mt-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Option</span>
                  </button>
                )}
              </div>

              {/* Deadline */}
              <div className="grid grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Deadline Date
                  </label>
                  <input
                    type="date"
                    required
                    value={pollForm.deadlineDate}
                    onChange={(e) => setPollForm({ ...pollForm, deadlineDate: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Deadline Time
                  </label>
                  <input
                    type="time"
                    required
                    value={pollForm.deadlineTime}
                    onChange={(e) => setPollForm({ ...pollForm, deadlineTime: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                  />
                </div>
              </div>

              {/* Allow Response Editing */}
              <div className="pt-2 flex items-center justify-between">
                <span className="text-xs font-medium text-slate-700">Allow students to change response</span>
                <input
                  type="checkbox"
                  checked={pollForm.allow_response_editing}
                  onChange={(e) => setPollForm({ ...pollForm, allow_response_editing: e.target.checked })}
                  className="w-4 h-4 rounded text-indigo-600 border-slate-300"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsCreatePollOpen(false)}
                  className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createPollMutation.isPending}
                  className="px-5 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-md shadow-indigo-100 disabled:opacity-50"
                >
                  {createPollMutation.isPending ? 'Creating Poll...' : 'Create & Generate Link'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ADD STUDENT MODAL */}
      {isAddStudentOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in">
          <div className="bg-white rounded-3xl max-w-xl w-full p-6 md:p-8 shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Add Student to {classData.name}</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Enroll registered students from the institutional database.
                </p>
              </div>
              <button
                onClick={() => {
                  setIsAddStudentOpen(false);
                  setStudentDirectoryQuery('');
                  setManualRegNo('');
                }}
                className="p-2 text-slate-400 hover:text-slate-600 rounded-xl hover:bg-slate-100 transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Method 1: Directory Search */}
            <div className="space-y-3">
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                1. Search Directory by Name, Reg Number, or Email
              </label>
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={studentDirectoryQuery}
                  onChange={(e) => setStudentDirectoryQuery(e.target.value)}
                  placeholder="Type at least 2 characters (e.g. Priya or 23AD)..."
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                />
              </div>

              {isSearchingDirectory && (
                <p className="text-xs text-slate-500 italic pl-1">Searching directory...</p>
              )}

              {searchResults && searchResults.length > 0 && (
                <div className="divide-y divide-slate-100 border border-slate-200 rounded-2xl max-h-56 overflow-y-auto bg-slate-50/50">
                  {searchResults.map((st) => {
                    const isAlreadyEnrolled = students?.some((m) => m.user_id === st.id);
                    return (
                      <div key={st.id} className="p-3.5 flex items-center justify-between gap-3 hover:bg-white transition-colors">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm text-slate-900">{st.name}</span>
                            <span className="font-mono text-xs px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700">
                              {st.register_number || 'No Reg #'}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5">
                            {st.department || 'N/A'} • {st.email} {st.phone_number ? `• ${st.phone_number}` : ''}
                          </p>
                        </div>

                        {isAlreadyEnrolled ? (
                          <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-lg">
                            Enrolled
                          </span>
                        ) : (
                          <button
                            onClick={() => addStudentMutation.mutate({ student_id: st.id })}
                            disabled={addStudentMutation.isPending}
                            className="inline-flex items-center gap-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-xs transition-all active:scale-95 disabled:opacity-50"
                          >
                            <Plus className="w-3.5 h-3.5" />
                            <span>Add</span>
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {searchResults && searchResults.length === 0 && studentDirectoryQuery.trim().length >= 2 && !isSearchingDirectory && (
                <p className="text-xs text-slate-400 italic pl-1">No matching students found in directory.</p>
              )}
            </div>

            <div className="relative flex py-1 items-center">
              <div className="flex-grow border-t border-slate-200" />
              <span className="flex-shrink mx-4 text-xs font-semibold text-slate-400 uppercase">Or Direct Enroll</span>
              <div className="flex-grow border-t border-slate-200" />
            </div>

            {/* Method 2: Direct Register Number */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!manualRegNo.trim()) return;
                addStudentMutation.mutate({ register_number: manualRegNo.trim().toUpperCase() });
              }}
              className="space-y-3"
            >
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                2. Enroll by Official Register Number
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={manualRegNo}
                  onChange={(e) => setManualRegNo(e.target.value)}
                  placeholder="e.g. 23AD020"
                  className="flex-1 px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-mono focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 uppercase"
                />
                <button
                  type="submit"
                  disabled={!manualRegNo.trim() || addStudentMutation.isPending}
                  className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-xl shadow-xs transition-all disabled:opacity-50"
                >
                  {addStudentMutation.isPending ? 'Enrolling...' : 'Enroll Student'}
                </button>
              </div>
            </form>

            <div className="pt-2 border-t border-slate-100 flex justify-end">
              <button
                type="button"
                onClick={() => {
                  setIsAddStudentOpen(false);
                  setStudentDirectoryQuery('');
                  setManualRegNo('');
                }}
                className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-xl"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* WhatsApp Share Modal */}
      <WhatsAppShareModal
        isOpen={shareModalData.isOpen}
        onClose={() => setShareModalData({ ...shareModalData, isOpen: false })}
        classNameTitle={shareModalData.classNameTitle}
        question={shareModalData.question}
        shareUrl={shareModalData.shareUrl}
        whatsappShareUrl={shareModalData.whatsappShareUrl}
      />
    </div>
  );
};
