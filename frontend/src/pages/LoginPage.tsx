import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { getErrorMessage } from '@/services/api';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname ?? '/dashboard';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await login({ email, password });
      navigate(from, { replace: true });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4">
      <div className="w-full max-w-sm animate-fade-in">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2.5 mb-8">
          <div className="w-8 h-8 rounded-md bg-brand flex items-center justify-center">
            <svg width="18" height="18" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M8 2L14 5.5V10.5L8 14L2 10.5V5.5L8 2Z" stroke="white" strokeWidth="1.5" strokeLinejoin="round"/>
              <circle cx="8" cy="8" r="2" fill="white"/>
            </svg>
          </div>
          <span className="font-semibold text-base tracking-tight">CloudPilot</span>
        </div>

        <div className="card p-6">
          <h1 className="text-lg font-semibold mb-1">Welcome back</h1>
          <p className="text-sm text-text-muted mb-6">Sign in to your account</p>

          {error && (
            <div className="bg-accent-red/10 border border-accent-red/20 rounded-md px-3 py-2.5 mb-4">
              <p className="text-sm text-accent-red">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" id="login-form">
            <Input
              id="login-email"
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              required
            />
            <Input
              id="login-password"
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              required
            />
            <Button
              type="submit"
              id="login-submit"
              isLoading={isLoading}
              className="w-full mt-1"
            >
              Sign In
            </Button>
          </form>
        </div>

        <p className="text-center text-sm text-text-muted mt-4">
          Don't have an account?{' '}
          <Link to="/register" id="login-register-link" className="text-brand-light hover:underline">
            Create one
          </Link>
        </p>
        <p className="text-center text-xs text-text-muted mt-2">
          <Link to="/" className="hover:text-text-secondary transition-colors">← Back to home</Link>
        </p>
      </div>
    </div>
  );
}
