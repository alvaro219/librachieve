import { useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import { refreshSession, setAccessToken } from "../api/client";
import { authApi, usersApi } from "../api/endpoints";
import type { TokenResponse, UserMe } from "../api/types";

interface AuthState {
  user: UserMe | null;
  loading: boolean;
  login: (login: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  /** Re-reads the session cookie (used after the Steam redirect) and the current user. */
  reload: () => Promise<void>;
  setUser: (user: UserMe) => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserMe | null>(null);
  const [loading, setLoading] = useState(true);
  const queryClient = useQueryClient();

  const reload = useCallback(async () => {
    try {
      setUser((await refreshSession()) ? await usersApi.me() : null);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const startSession = useCallback(async (tokens: TokenResponse) => {
    setAccessToken(tokens.access_token);
    setUser(await usersApi.me());
  }, []);

  const value: AuthState = {
    user,
    loading,
    reload,
    setUser,
    login: async (login, password) => startSession(await authApi.login(login, password)),
    register: async (username, email, password) =>
      startSession(await authApi.register(username, email, password)),
    logout: async () => {
      await authApi.logout().catch(() => undefined);
      setAccessToken(null);
      setUser(null);
      queryClient.clear();
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
