"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  getToken,
  getUser,
  isLoggedIn,
  loginWithGoogle,
  logout as authLogout,
  setUser as storeUser,
  type UserInfo,
} from "@/lib/auth";

interface AuthContextType {
  user: UserInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (idToken: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => {},
  logout: () => {},
  refreshUser: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount: check localStorage for existing session
  useEffect(() => {
    if (isLoggedIn()) {
      const stored = getUser();
      if (stored) {
        setUser(stored);
      }
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (idToken: string) => {
    const result = await loginWithGoogle(idToken);
    setUser(result.user);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    authLogout();
  }, []);

  const refreshUser = useCallback(async () => {
    const token = getToken();
    if (!token) return;

    try {
      const res = await fetch("/api/user", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.status === 401) {
        // Token expired — force logout
        setUser(null);
        authLogout();
        return;
      }

      if (res.ok) {
        const freshUser: UserInfo = await res.json();
        setUser(freshUser);
        storeUser(freshUser);
      }
    } catch {
      // Network error — keep existing user data
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
