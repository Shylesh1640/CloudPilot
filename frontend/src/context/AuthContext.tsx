import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { authService } from '@/services/authService';
import { clearToken, getToken, setToken } from '@/services/api';
import type { AuthContextValue, LoginPayload, RegisterPayload, User } from '@/types';

// ─────────────────────────────────────────────────────────────────────────────
//  Auth Context
// ─────────────────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(getToken);
  const [isLoading, setIsLoading] = useState(true);

  // On mount: if a token exists, fetch the current user to hydrate context
  useEffect(() => {
    const init = async () => {
      const storedToken = getToken();
      if (!storedToken) {
        setIsLoading(false);
        return;
      }
      try {
        const currentUser = await authService.me();
        setUser(currentUser);
      } catch {
        // Token is invalid or expired — clear it
        clearToken();
        setTokenState(null);
      } finally {
        setIsLoading(false);
      }
    };
    init();
  }, []);

  const login = useCallback(async (payload: LoginPayload) => {
    const { access_token } = await authService.login(payload);
    setToken(access_token);
    setTokenState(access_token);
    const currentUser = await authService.me();
    setUser(currentUser);
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    await authService.register(payload);
    // Auto-login after successful registration
    await login({ email: payload.email, password: payload.password });
  }, [login]);

  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuthContext must be used inside <AuthProvider>');
  }
  return ctx;
}
