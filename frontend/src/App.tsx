import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { DashboardLayout } from './layouts/DashboardLayout';

// Public Pages
import { LandingPage } from './pages/public/LandingPage';
import { LoginPage } from './pages/public/LoginPage';
import { PublicPollPage } from './pages/public/PublicPollPage';

// Student Pages
import { StudentDashboard } from './pages/student/StudentDashboard';
import { StudentPollsPage } from './pages/student/StudentPollsPage';
import { StudentHistoryPage } from './pages/student/StudentHistoryPage';
import { StudentProfilePage } from './pages/student/StudentProfilePage';

// Teacher / Faculty Pages
import { TeacherDashboard } from './pages/teacher/TeacherDashboard';
import { TeacherClassesPage } from './pages/teacher/TeacherClassesPage';
import { TeacherClassDetailPage } from './pages/teacher/TeacherClassDetailPage';
import { TeacherPollDetailPage } from './pages/teacher/TeacherPollDetailPage';
import { TeacherProfilePage } from './pages/teacher/TeacherProfilePage';

// REP Pages
import { RepDashboard } from './pages/rep/RepDashboard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30, // 30 seconds
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/poll/:publicId" element={<PublicPollPage />} />

              {/* Protected Student Portal */}
              <Route
                path="/student"
                element={
                  <ProtectedRoute allowedRoles={['STUDENT']}>
                    <DashboardLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/student/dashboard" replace />} />
                <Route path="dashboard" element={<StudentDashboard />} />
                <Route path="polls" element={<StudentPollsPage />} />
                <Route path="history" element={<StudentHistoryPage />} />
                <Route path="profile" element={<StudentProfilePage />} />
              </Route>

              {/* Protected Faculty Portal */}
              <Route
                path="/teacher"
                element={
                  <ProtectedRoute allowedRoles={['FACULTY', 'TEACHER']}>
                    <DashboardLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/teacher/dashboard" replace />} />
                <Route path="dashboard" element={<TeacherDashboard />} />
                <Route path="classes" element={<TeacherClassesPage />} />
                <Route path="classes/:id" element={<TeacherClassDetailPage />} />
                <Route path="polls/:id" element={<TeacherPollDetailPage />} />
                <Route path="profile" element={<TeacherProfilePage />} />
              </Route>

              {/* Protected Class REP Portal */}
              <Route
                path="/rep"
                element={
                  <ProtectedRoute allowedRoles={['STUDENT']}>
                    <DashboardLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/rep/dashboard" replace />} />
                <Route path="dashboard" element={<RepDashboard />} />
                <Route path="classes" element={<TeacherClassesPage />} />
                <Route path="classes/:id" element={<TeacherClassDetailPage />} />
                <Route path="polls/:id" element={<TeacherPollDetailPage />} />
              </Route>

              {/* Catch-all redirect */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
};

export default App;
