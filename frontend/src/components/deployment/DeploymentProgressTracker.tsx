import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { CheckCircle2, Layers, Network, HardDrive, Cpu, Play, AlertCircle } from 'lucide-react';
import type { DeploymentRead, DeploymentStatus } from '@/types';

interface Props {
  deployment: DeploymentRead;
}

const STEPS: { status: DeploymentStatus; label: string; icon: any }[] = [
  { status: 'PREPARING', label: 'Validate Plan Topology', icon: Layers },
  { status: 'CREATING_NETWORK', label: 'Create Docker Network', icon: Network },
  { status: 'CREATING_VOLUMES', label: 'Create Persistent Volumes', icon: HardDrive },
  { status: 'BUILDING', label: 'Build & Pull Container Images', icon: Cpu },
  { status: 'STARTING', label: 'Instantiate & Start Services', icon: Play },
];

function getStepState(stepStatus: DeploymentStatus, currentStatus: DeploymentStatus) {
  const order: DeploymentStatus[] = [
    'PENDING',
    'PREPARING',
    'CREATING_NETWORK',
    'CREATING_VOLUMES',
    'BUILDING',
    'CREATING_SERVICES',
    'STARTING',
    'RUNNING',
  ];

  const currentIdx = order.indexOf(currentStatus);
  const stepIdx = order.indexOf(stepStatus);

  if (currentStatus === 'FAILED') return 'error';
  if (currentStatus === 'RUNNING' || (currentIdx > stepIdx && currentIdx !== -1)) return 'completed';
  if (currentStatus === stepStatus) return 'active';
  return 'pending';
}

export function DeploymentProgressTracker({ deployment }: Props) {
  return (
    <div className="card p-5 space-y-4 animate-fade-in border-brand/30">
      {/* Top Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
            {deployment.status === 'RUNNING' ? (
              <span className="text-accent-green flex items-center gap-1.5 font-bold">
                <CheckCircle2 size={16} /> Container Deployment Live
              </span>
            ) : deployment.status === 'FAILED' ? (
              <span className="text-accent-red flex items-center gap-1.5 font-bold">
                <AlertCircle size={16} /> Deployment Failed
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <LoadingSpinner size="sm" /> Orchestrating Services (v{deployment.version})...
              </span>
            )}
          </h3>
          <p className="text-xs text-text-muted mt-0.5">
            CloudPilot Container Orchestrator · {deployment.progress}% Complete
          </p>
        </div>

        <span className="font-mono text-xs text-brand-light bg-surface-overlay border border-surface-border px-2 py-1 rounded">
          {deployment.status}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-surface-overlay h-2 rounded-full overflow-hidden border border-surface-border">
        <div
          className={`h-full transition-all duration-300 ease-out ${
            deployment.status === 'FAILED' ? 'bg-accent-red' : 'bg-brand'
          }`}
          style={{ width: `${deployment.progress}%` }}
        />
      </div>

      {/* Step Timeline */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 pt-2 border-t border-surface-border">
        {STEPS.map((step) => {
          const state = getStepState(step.status, deployment.status);
          const Icon = step.icon;

          return (
            <div
              key={step.status}
              className={`p-2.5 rounded-md border text-xs flex items-center gap-2 transition-all ${
                state === 'completed'
                  ? 'bg-accent-green/10 border-accent-green/30 text-accent-green'
                  : state === 'active'
                  ? 'bg-brand/10 border-brand/40 text-brand-light font-semibold ring-1 ring-brand/30'
                  : state === 'error'
                  ? 'bg-accent-red/10 border-accent-red/30 text-accent-red'
                  : 'bg-surface-overlay border-surface-border text-text-muted opacity-60'
              }`}
            >
              <Icon size={14} className="flex-shrink-0" />
              <span className="text-[11px] truncate">{step.label}</span>
            </div>
          );
        })}
      </div>

      {/* Deployment Log Stream Snippet */}
      {deployment.logs && deployment.logs.length > 0 && (
        <div className="p-3 bg-surface-base rounded border border-surface-border font-mono text-[11px] max-h-28 overflow-y-auto space-y-1">
          {deployment.logs.map((log, idx) => (
            <div key={idx} className="flex items-start gap-2 text-text-secondary">
              <span className="text-text-muted select-none">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
              <span className="text-brand-light">{log.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
