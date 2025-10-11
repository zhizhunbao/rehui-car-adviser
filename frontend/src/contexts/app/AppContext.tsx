import React, { createContext, useContext, ReactNode, useState, useCallback } from 'react';

// 应用全局状态接口
interface AppState {
  theme: 'light' | 'dark';
  language: string;
  user: {
    id: string;
    name: string;
    email: string;
  } | null;
  isLoading: boolean;
  error: string | null;
}

// 应用状态操作接口
interface AppActions {
  setTheme: (theme: 'light' | 'dark') => void;
  setLanguage: (language: string) => void;
  setUser: (user: AppState['user']) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

// 完整的应用上下文类型
type AppContextType = AppState & AppActions;

// 创建应用上下文
export const AppContext = createContext<AppContextType | undefined>(undefined);

// AppProvider 组件
export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [language, setLanguage] = useState<string>('zh-CN');
  const [user, setUser] = useState<AppState['user']>(null);
  const [isLoading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const contextValue: AppContextType = {
    theme,
    language,
    user,
    isLoading,
    error,
    setTheme,
    setLanguage,
    setUser,
    setLoading,
    setError,
    clearError,
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};

// 应用上下文Hook
export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

// 保持向后兼容
export const useAppContext = useApp;
