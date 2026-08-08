import { Activity, ShieldCheck, AlertTriangle, XCircle, Clock } from 'lucide-react';
import type { DeploymentHealthRead, HealthStatus } from '@/types';

interface Props {
  health: DeploymentHealthRead;
}

export function DeploymentHealthCard({ health }: Props) {
  const getBadge = (status: HealthStatus) => {
    switch (status) {
      case 'HEALTHY':
        return {
          icon: ShieldCheck,
          text: 'HEALTHY / READY',
          cls: 'bg-accent-green/10 text-accent-green border-accent-green/30',
        };
      case 'DEGRADED':
        return {
          icon: AlertTriangle,
          text: 'DEGRADED',
          cls: 'bg-accent-yellow/10 text-accent-yellow border-accent-yellow/30',
        };
      case 'UNHEALTHY':
      case 'FAILED':
        return {
          icon: XCircle,
          text: status,
          cls: 'bg-accent-red/10 text-accent-red border-accent-red/30',
        };
      default:
        return {
          icon: Activity,
          text: 'STARTING / UNKNOWN',
          cls: 'bg-surface-overlay text-text-muted border-surface-border',
        };
    }
  };

  const badge = getBadge(health.overall_health);
  const Icon = badge.icon;

  const totalServices = Object.keys(health.services).length;
  const healthyCount = Object.values(health.services).filter((s) => s === 'HEALTHY').length;

  return (
    <div className="card p-5 border-surface-border bg-surface-overlay/40 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-lg border ${badge.cls}`}>
            <Icon size={20} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-text-primary">Deployment Health Engine (Phase 5)</h3>
            <p className="text-xs text-text-muted">Liveness, Readiness, TCP & HTTP Health Metrics</p>
          </div>
        </div>

        <span className={`tag border px-3 py-1 text-xs font-bold ${badge.cls}`}>
          ● {badge.text}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
        <div className="p-3 rounded-md bg-surface-card border border-surface-border">
          <span className="text-[11px] text-text-muted">Healthy Services</span>
          <p className="text-sm font-bold font-mono text-accent-green mt-0.5">
            {healthyCount} / {totalServices}
          </p>
        </div>

        <div className="p-3 rounded-md bg-surface-card border border-surface-border">
          <span className="text-[11px] text-text-muted">Average Latency</span>
          <p className="text-sm font-bold font-mono text-brand-light mt-0.5 flex items-center gap-1">
            <Clock size={12} />
            {health.avg_latency_ms ? `${health.avg_latency_ms} ms` : 'N/A'}
          </p>
        </div>

        <div className="p-3 rounded-md bg-surface-card border border-surface-border">
          <span className="text-[11px] text-text-muted">Startup Grace Period</span>
          <p className="text-sm font-bold font-mono text-text-secondary mt-0.5">30 sec</p>
        </div>

        <div className="p-3 rounded-md bg-surface-card border border-surface-border">
          <span className="text-[11px] text-text-muted">Check Interval</span>
          <p className="text-sm font-bold font-mono text-text-secondary mt-0.5">10 sec</p>
        </div>
      </div>
    </div>
  );
}
