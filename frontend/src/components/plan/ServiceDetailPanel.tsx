import { X, Layers, Activity, Cpu, Shield, Globe, Box, Database, Terminal, RefreshCw, Play } from 'lucide-react';
import type { DeploymentServiceInfo, HealthCheck, InfrastructurePlan, ResourceProfile, ServiceDefinition } from '@/types';
import { Button } from '@/components/ui/Button';

interface Props {
  service: ServiceDefinition;
  plan: InfrastructurePlan;
  deploymentService?: DeploymentServiceInfo;
  onClose: () => void;
  onRestartService?: (serviceId: string) => void;
  onOpenLogs?: (serviceId: string, serviceName: string) => void;
}

export function ServiceDetailPanel({
  service,
  plan,
  deploymentService,
  onClose,
  onRestartService,
  onOpenLogs,
}: Props) {
  // Find associated resource profile & health check
  const resProfile: ResourceProfile | undefined = plan.resource_profiles.find((r) => r.service === service.id);
  const healthCheck: HealthCheck | undefined = plan.health_checks.find((h) => h.service === service.id);
  const envVars = plan.environment.find((e) => e.service === service.id)?.variables || [];

  return (
    <div className="card p-5 space-y-5 animate-fade-in border-brand/40 shadow-xl relative">
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 text-text-muted hover:text-text-primary p-1 rounded-md transition-colors"
      >
        <X size={16} />
      </button>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-base font-bold text-text-primary">{service.name}</h3>
            <span className="tag bg-surface-border text-text-secondary capitalize">{service.type}</span>
            {deploymentService ? (
              <span className={`tag border text-xs font-semibold ${
                deploymentService.actual_state === 'RUNNING'
                  ? 'bg-accent-green/10 text-accent-green border-accent-green/20'
                  : 'bg-accent-red/10 text-accent-red border-accent-red/20'
              }`}>
                ● {deploymentService.actual_state}
              </span>
            ) : service.public ? (
              <span className="tag bg-accent-green/10 text-accent-green border border-accent-green/20">Public</span>
            ) : (
              <span className="tag bg-surface-overlay text-text-muted">Private</span>
            )}
          </div>
          <p className="text-xs text-text-muted font-mono">{service.source_path || `/${service.id}`}</p>
        </div>

        {/* Action Buttons */}
        {deploymentService && (
          <div className="flex items-center gap-2 mr-6">
            {onOpenLogs && (
              <Button
                variant="secondary"
                onClick={() => onOpenLogs(service.id, service.name)}
                className="text-xs gap-1 py-1 px-2.5"
              >
                <Terminal size={12} />
                Logs
              </Button>
            )}
            {onRestartService && (
              <Button
                variant="secondary"
                onClick={() => onRestartService(service.id)}
                className="text-xs gap-1 py-1 px-2.5"
              >
                <RefreshCw size={12} />
                Restart
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Specs Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 bg-surface-overlay rounded-md border border-surface-border">
        <div>
          <p className="data-label">Port / Protocol</p>
          <p className="text-xs font-mono font-semibold text-brand-light mt-0.5">
            {service.port ? `${service.port} / ${service.protocol}` : 'Internal'}
          </p>
        </div>
        <div>
          <p className="data-label">Replicas</p>
          <p className="text-xs font-mono font-semibold mt-0.5">
            {service.replicas.min}–{service.replicas.max} (init: {service.replicas.initial})
          </p>
        </div>
        <div>
          <p className="data-label">Scaling</p>
          <p className="text-xs font-semibold mt-0.5">
            {service.scalable ? <span className="text-accent-green">Horizontal</span> : 'Fixed (1x)'}
          </p>
        </div>
        <div>
          <p className="data-label">Confidence</p>
          <p className="text-xs font-mono font-semibold mt-0.5 text-accent-green">
            {Math.round(service.confidence * 100)}%
          </p>
        </div>
      </div>

      {/* Resources & Health Check */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Resource Allocation */}
        <div className="p-3 bg-surface-overlay rounded-md border border-surface-border space-y-2">
          <h4 className="text-xs font-semibold text-text-primary flex items-center gap-1.5">
            <Cpu size={13} className="text-brand-light" />
            Recommended Resources
          </h4>
          {resProfile ? (
            <div className="text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-text-muted">CPU Limit:</span>
                <span className="font-mono text-text-primary">{resProfile.cpu} cores</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Memory Limit:</span>
                <span className="font-mono text-text-primary">{resProfile.memory}</span>
              </div>
              <p className="text-[10px] text-text-muted pt-1 border-t border-surface-border/50">
                Reason: {resProfile.reason}
              </p>
            </div>
          ) : (
            <p className="text-xs text-text-muted">Baseline allocation.</p>
          )}
        </div>

        {/* Health Check */}
        <div className="p-3 bg-surface-overlay rounded-md border border-surface-border space-y-2">
          <h4 className="text-xs font-semibold text-text-primary flex items-center gap-1.5">
            <Activity size={13} className="text-accent-green" />
            Health Check Policy
          </h4>
          {healthCheck ? (
            <div className="text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-text-muted">Endpoint:</span>
                <span className="font-mono text-brand-light">{healthCheck.path || '/'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Interval / Timeout:</span>
                <span className="font-mono text-text-primary">{healthCheck.interval_seconds}s / {healthCheck.timeout_seconds}s</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Failure Threshold:</span>
                <span className="font-mono text-text-primary">{healthCheck.failure_threshold} consecutive</span>
              </div>
            </div>
          ) : (
            <p className="text-xs text-text-muted">No health endpoint specified.</p>
          )}
        </div>
      </div>

      {/* Environment Variables */}
      {envVars.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-text-primary mb-2 flex items-center gap-1.5">
            <Terminal size={13} className="text-brand-light" />
            Environment Variables ({envVars.length})
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {envVars.map((v) => (
              <span key={v.name} className={`tag border text-[11px] font-mono ${v.secret ? 'bg-accent-red/10 text-accent-red border-accent-red/20' : 'bg-surface-overlay text-text-secondary border-surface-border'}`}>
                {v.name} {v.secret && '🔒'}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Evidence */}
      {service.evidence.length > 0 && (
        <div className="pt-2 border-t border-surface-border">
          <p className="text-[11px] font-semibold text-text-muted mb-1">Phase 2 Detection Evidence:</p>
          <ul className="space-y-0.5">
            {service.evidence.map((ev, idx) => (
              <li key={idx} className="text-[11px] text-text-secondary flex items-center gap-1.5">
                <span className="text-brand-light">•</span>
                <span>{ev}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
