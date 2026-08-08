import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { getErrorMessage } from '@/services/api';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

interface FormErrors {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

function validate(
  name: string,
  email: string,
  password: string,
  confirmPassword: string
): FormErrors {
  const errors: FormErrors = {};
  if (!name.trim()) errors.name = 'Name is required';
  if (!email.trim()) errors.email = 'Email is required';
  if (password.length < 8) errors.password = 'Password must be at least 8 characters';
  if (password !== confirmPassword) errors.confirmPassword = 'Passwords do not match';
  return errors;
}

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [apiError, setApiError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError('');

    const errors = validate(name, email, password, confirmPassword);
    setFormErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setIsLoading(true);
    try {
      await register({ name, email, password });
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setApiError(getErrorMessage(err));
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
          <h1 className="text-lg font-semibold mb-1">Create an account</h1>
          <p className="text-sm text-text-muted mb-6">Join CloudPilot to start deploying</p>

          {apiError && (
            <div className="bg-accent-red/10 border border-accent-red/20 rounded-md px-3 py-2.5 mb-4">
              <p className="text-sm text-accent-red">{apiError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" id="register-form">
            <Input
              id="register-name"
              label="Full Name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Jane Smith"
              autoComplete="name"
              error={formErrors.name}
              required
            />
            <Input
              id="register-email"
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="jane@example.com"
              autoComplete="email"
              error={formErrors.email}
              required
            />
            <Input
              id="register-password"
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min. 8 characters"
              autoComplete="new-password"
              error={formErrors.password}
              required
            />
            <Input
              id="register-confirm-password"
              label="Confirm Password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Repeat password"
              autoComplete="new-password"
              error={formErrors.confirmPassword}
              required
            />
            <Button
              type="submit"
              id="register-submit"
              isLoading={isLoading}
              className="w-full mt-1"
            >
              Create Account
            </Button>
          </form>
        </div>

        <p className="text-center text-sm text-text-muted mt-4">
          Already have an account?{' '}
          <Link to="/login" id="register-login-link" className="text-brand-light hover:underline">
            Sign in
          </Link>
        </p>
        <p className="text-center text-xs text-text-muted mt-2">
          <Link to="/" className="hover:text-text-secondary transition-colors">← Back to home</Link>
        </p>
      </div>
    </div>
  );
}
