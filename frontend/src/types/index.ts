export type UserRole = 'FACULTY' | 'STUDENT' | 'TEACHER';
export type UserStatus = 'PENDING' | 'ACTIVE' | 'SUSPENDED' | 'DEACTIVATED';
export type PollStatus = 'DRAFT' | 'ACTIVE' | 'CLOSED' | 'ARCHIVED';

export interface StudentProfile {
  id: number;
  register_number: string;
  department: string;
  year: number;
  section: string;
  phone_number?: string;
}

export interface TeacherProfile {
  id: number;
  employee_id: string;
  department: string;
  phone_number?: string;
}

export interface RepAssignment {
  class_id: number;
  class_name: string;
}

export interface TeacherAssignment {
  class_id: number;
  class_name: string;
}

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  email_verified: boolean;
  created_at: string;
  last_login_at?: string;
  student_profile?: StudentProfile;
  teacher_profile?: TeacherProfile;
  rep_classes?: RepAssignment[];
  teacher_classes?: TeacherAssignment[];
}

export interface ClassItem {
  id: number;
  name: string;
  department: string;
  year: number;
  section: string;
  academic_year: string;
  class_code: string;
  is_active: boolean;
  allow_rep_poll_creation: boolean;
  created_at: string;
  total_students: number;
  total_teachers: number;
  total_reps: number;
  active_polls: number;
  is_rep: boolean;
  is_teacher: boolean;
  assigned_teachers?: ClassTeacherDetail[];
}

export interface ClassTeacherDetail {
  id?: number;
  teacher_id: number;
  name: string;
  email: string;
  employee_id?: string;
}

export interface ClassMember {
  id: number;
  user_id: number;
  name: string;
  email: string;
  register_number?: string;
  department?: string;
  year?: number;
  section?: string;
  phone_number?: string;
  joined_at: string;
  is_rep: boolean;
  is_active: boolean;
  is_muted: boolean;
}

export interface StudentSearchItem {
  id: number;
  name: string;
  email: string;
  register_number?: string;
  department?: string;
  year?: number;
  section?: string;
  phone_number?: string;
}

export interface MessageLogItem {
  id: number;
  poll_id: number;
  student_id: number;
  student_name: string;
  recipient_phone: string;
  message_type: string;
  provider: string;
  provider_message_id?: string;
  delivery_status: string;
  error_message?: string;
  sent_at: string;
}

export interface ReminderResponse {
  total_targeted: number;
  sent_count: number;
  failed_count: number;
  results: MessageLogItem[];
}

export interface PollOption {
  id: number;
  option_text: string;
  position: number;
  votes_count: number;
  percentage: number;
}

export interface Poll {
  id: number;
  public_id: string;
  class_id: number;
  class_name: string;
  creator_id: number;
  creator_name: string;
  question: string;
  deadline: string;
  status: PollStatus;
  allow_response_editing: boolean;
  created_at: string;
  options: PollOption[];
  has_responded: boolean;
  selected_option_id?: number;
  total_students: number;
  total_responses: number;
  completion_rate: number;
  is_closed: boolean;
  share_url: string;
  whatsapp_share_url: string;
}

export interface ParticipantDetail {
  student_id: number;
  name: string;
  register_number?: string;
  email: string;
  phone_number?: string;
  option_id?: number;
  option_text?: string;
  submitted_at?: string;
}

export interface PollParticipantsResponse {
  poll_id: number;
  public_id: string;
  creator_id: number;
  question: string;
  class_id: number;
  class_name: string;
  deadline: string;
  is_closed: boolean;
  total_students: number;
  completed_count: number;
  pending_count: number;
  completion_rate: number;
  done_students: ParticipantDetail[];
  not_done_students: ParticipantDetail[];
  options: PollOption[];
}

export interface StudentDashboardStats {
  active_polls_count: number;
  completed_polls_count: number;
  pending_polls_count: number;
  completion_rate: number;
}

export interface StudentHistoryItem {
  poll_id: number;
  public_id: string;
  question: string;
  class_name: string;
  deadline: string;
  is_closed: boolean;
  is_done: boolean;
  submitted_at?: string;
  selected_option_text?: string;
}

export interface TeacherDashboardStats {
  my_classes_count: number;
  total_students: number;
  active_polls: number;
  average_completion_rate: number;
}

export type FacultyDashboardStats = TeacherDashboardStats;
