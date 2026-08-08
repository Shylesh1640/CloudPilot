import { clsx } from 'clsx';
import type { ProjectStatus } from '@/types';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'purple';
  className?: string;
}

const variantClasses = {
  default: 'bg-surface-border text-text-secondary',
  success: 'bg-accent-green/10 text-accent-green border border-accent-green/20',
  warning: 'bg-accent-yellow/10 text-accent-yellow border border-accent-yellow/20',
  error: 'bg-accent-red/10 text-accent-red border border-accent-red/20',
  info: 'bg-brand/10 text-brand-light border border-brand/20',
  purple: 'bg-accent-purple/10 text-accent-purple border border-accent-purple/20',
};

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span className={clsx('tag', variantClasses[variant], className)}>
      {children}
    </span>
  );
}

// ── Status badge for ProjectStatus enum ──────────────────────────────────────

const statusConfig: Record<ProjectStatus, { label: string; variant: BadgeProps['variant']; dot: string }> = {
  CREATED:   { label: 'Created',   variant: 'default',  dot: 'bg-text-muted' },
  ANALYZING: { label: 'Analyzing', variant: 'purple',   dot: 'bg-accent-purple animate-pulse' },
  DEPLOYING: { label: 'Deploying', variant: 'info',     dot: 'bg-brand animate-pulse' },
  RUNNING:   { label: 'Running',   variant: 'success',  dot: 'bg-accent-green' },
  FAILED:    { label: 'Failed',    variant: 'error',    dot: 'bg-accent-red' },
  STOPPED:   { label: 'Stopped',   variant: 'warning',  dot: 'bg-accent-yellow' },
};

export function StatusBadge({ status }: { status: ProjectStatus }) {
  const cfg = statusConfig[status];
  return (
    <Badge variant={cfg.variant} className="gap-1.5">
      <span className={clsx('status-dot', cfg.dot)} />
      {cfg.label}
    </Badge>
  );
}
