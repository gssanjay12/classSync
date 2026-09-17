import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../api/client';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (accessToken: string, refreshToken: string, userData: Partial<User>) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  isRepOfClass: (classId: number) => boolean;
  isTeacherOfClass: (classId: number) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('classpoll_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('classpoll_access_token'));
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const res = await api.get('/auth/me');
      setUser(res.data);
      localStorage.setItem('classpoll_user', JSON.stringify(res.data));
    } catch {
      // If unauthorized, clean up
      setUser(null);
      setToken(null);
      localStorage.removeItem('classpoll_access_token');
      localStorage.removeItem('classpoll_refresh_token');
      localStorage.removeItem('classpoll_user');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (token) {
      refreshUser();
    } else {
      setIsLoading(false);
    }
  }, [token, refreshUser]);

  const login = async (accessToken: string, refreshToken: string) => {
    localStorage.setItem('classpoll_access_token', accessToken);
    localStorage.setItem('classpoll_refresh_token', refreshToken);
    setToken(accessToken);
    await refreshUser();
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem('classpoll_refresh_token');
    if (refreshToken) {
      try {
        await api.post('/auth/logout', { refresh_token: refreshToken });
      } catch {
        // Ignore logout errors
      }
    }
    localStorage.removeItem('classpoll_access_token');
    localStorage.removeItem('classpoll_refresh_token');
    localStorage.removeItem('classpoll_user');
    setUser(null);
    setToken(null);
  };

  const isRepOfClass = (classId: number): boolean => {
    if (!user) return false;
    return Boolean(user.rep_classes?.some((rc) => rc.class_id === classId));
  };

  const isTeacherOfClass = (classId: number): boolean => {
    if (!user) return false;
    return Boolean(user.teacher_classes?.some((tc) => tc.class_id === classId));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        logout,
        refreshUser,
        isRepOfClass,
        isTeacherOfClass,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
