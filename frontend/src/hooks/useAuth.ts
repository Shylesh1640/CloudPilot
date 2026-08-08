import { useAuthContext } from '@/context/AuthContext';

/**
 * Convenience hook that exposes auth state and actions.
 * Use this in components instead of useAuthContext directly.
 */
export function useAuth() {
  return useAuthContext();
}
