import React, { ReactNode, useState, useCallback } from 'react';
import { AppContext } from './AppContext';

interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  // 应用全局状态
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [language, setLanguage] = useState<string>('zh-CN');
  const [user, setUser] = useState<{
    id: string;
    name: string;
    email: string;
  } | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // 状态操作方法
  const handleSetTheme = useCallback((newTheme: 'light' | 'dark') => {
    setTheme(newTheme);
    // 可以在这里添加主题切换的副作用，如保存到localStorage
  }, []);

  const handleSetLanguage = useCallback((newLanguage: string) => {
    setLanguage(newLanguage);
    // 可以在这里添加语言切换的副作用
  }, []);

  const handleSetUser = useCallback((newUser: typeof user) => {
    setUser(newUser);
  }, []);

  const handleSetLoading = useCallback((loading: boolean) => {
    setIsLoading(loading);
  }, []);

  const handleSetError = useCallback((errorMessage: string | null) => {
    setError(errorMessage);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const contextValue = {
    // 状态
    theme,
    language,
    user,
    isLoading,
    error,
    // 操作方法
    setTheme: handleSetTheme,
    setLanguage: handleSetLanguage,
    setUser: handleSetUser,
    setLoading: handleSetLoading,
    setError: handleSetError,
    clearError,
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};
