import React, { useState } from 'react';
import { Link, useLocation, useNavigate, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  BookOpen,
  Vote,
  History,
  Shield,
  UserCircle,
  LogOut,
  Menu,
  X,
  FileSpreadsheet,
  CheckCircle,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Badge } from '../components/common/Badge';

export const DashboardLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Nav links based on role
  const getNavLinks = () => {
    if (!user) return [];

    if (user.role === 'FACULTY' || user.role === 'TEACHER') {
      return [
        { name: 'Dashboard', path: '/teacher/dashboard', icon: LayoutDashboard },
        { name: 'My Classes', path: '/teacher/classes', icon: BookOpen },
        { name: 'Profile', path: '/teacher/profile', icon: UserCircle },
      ];
    }

    // Student (check if REP)
    const isRep = user.rep_classes && user.rep_classes.length > 0;
    if (isRep) {
      return [
        { name: 'REP Dashboard', path: '/rep/dashboard', icon: LayoutDashboard },
        { name: 'My Class', path: '/rep/classes', icon: BookOpen },
        { name: 'My Polls', path: '/student/polls', icon: Vote },
        { name: 'Poll History', path: '/student/history', icon: History },
        { name: 'Profile', path: '/student/profile', icon: UserCircle },
      ];
    }

    return [
      { name: 'My Dashboard', path: '/student/dashboard', icon: LayoutDashboard },
      { name: 'Active Polls', path: '/student/polls', icon: Vote },
      { name: 'Poll History', path: '/student/history', icon: History },
      { name: 'Profile', path: '/student/profile', icon: UserCircle },
    ];
  };

  const navLinks = getNavLinks();
  const isFaculty = user?.role === 'FACULTY' || user?.role === 'TEACHER';
  const isRep = user?.rep_classes && user.rep_classes.length > 0;
  const roleLabel = isFaculty ? 'FACULTY' : isRep ? 'REP' : 'STUDENT';
  const badgeVariant = isFaculty ? 'teacher' : isRep ? 'rep' : 'student';

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 bg-white border-r border-slate-200">
        <div className="p-6 border-b border-slate-100 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold text-lg shadow-md shadow-indigo-200">
            CP
          </div>
          <div>
            <h1 className="font-bold text-slate-900 leading-tight">ClassPoll</h1>
            <p className="text-[11px] font-medium text-slate-400 tracking-wide uppercase">Institutional Portal</p>
          </div>
        </div>

        {/* User Role Card */}
        <div className="p-4 mx-4 mt-4 rounded-xl bg-slate-50 border border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm">
              {user?.name.charAt(0).toUpperCase()}
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-semibold text-slate-800 truncate">{user?.name}</p>
              <div className="mt-0.5">
                <Badge variant={badgeVariant}>
                  {roleLabel}
                </Badge>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
          {navLinks.map((item) => {
            const isActive = location.pathname.startsWith(item.path);
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-100'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer actions */}
        <div className="p-4 border-t border-slate-100">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3.5 py-2.5 rounded-xl text-sm font-medium text-slate-600 hover:bg-rose-50 hover:text-rose-600 transition-colors"
          >
            <LogOut className="w-4 h-4 text-slate-400 group-hover:text-rose-600" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Mobile Top Nav & Drawer */}
      <div className="md:hidden fixed top-0 inset-x-0 z-40 bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-bold text-sm">
            CP
          </div>
          <span className="font-bold text-slate-900 text-base">ClassPoll</span>
        </div>
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 text-slate-600 hover:bg-slate-100 rounded-lg"
        >
          {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {isMobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-30 bg-slate-900/40 pt-16 animate-in fade-in">
          <div className="bg-white p-6 space-y-4 border-b border-slate-200 shadow-xl">
            <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl">
              <div className="w-9 h-9 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm">
                {user?.name.charAt(0).toUpperCase()}
              </div>
              <div>
                <p className="font-semibold text-slate-800 text-sm">{user?.name}</p>
                <Badge variant={user?.role === 'FACULTY' || user?.role === 'TEACHER' ? 'teacher' : 'student'}>
                  {user?.role === 'TEACHER' ? 'FACULTY' : user?.role}
                </Badge>
              </div>
            </div>

            <nav className="space-y-1">
              {navLinks.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 hover:bg-slate-100"
                >
                  <item.icon className="w-4 h-4 text-slate-400" />
                  <span>{item.name}</span>
                </Link>
              ))}
              <button
                onClick={handleLogout}
                className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-medium text-rose-600 hover:bg-rose-50"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign Out</span>
              </button>
            </nav>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 md:pt-0 pt-16 overflow-y-auto">
        <div className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
