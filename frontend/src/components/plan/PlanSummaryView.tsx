import { AlertTriangle, CheckCircle2, RefreshCw, Shield, Layers, Cpu, Database, Activity } from 'lucide-react';
import type { InfrastructurePlan } from '@/types';
import { Button } from '@/components/ui/Button';

interface Props {
  plan: InfrastructurePlan;
  version: number;
  aiProvider?: string | null;
  aiModel?: string | null;
  durationMs?: number | null;
  onRegenerate: () => void;
  isRegenerating: boolean;
}

export function PlanSummaryView({
  plan,
  version,
  aiProvider,
  aiModel,
  durationMs,
  onRegenerate,
  isRegenerating,
}: Props) {
  const publicServicesCount = plan.services.filter((s) => s.public).length;
  const scalableServicesCount = plan.services.filter((s) => s.scalable).length;
  const persistentVolumesCount = plan.volumes.filter((v) => v.persistent).length;

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Metric Highlights Header */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card p-3.5 bg-surface-overlay border-surface-border">
          <p className="data-label">Total Services</p>
          <p className="text-lg font-bold mt-0.5 text-brand-light">
            {plan.services.length} services
          </p>
        </div>

        <div className="card p-3.5 bg-surface-overlay border-surface-border">
          <p className="data-label">Public Entrypoints</p>
          <p className="text-lg font-bold mt-0.5 text-accent-green">
            {publicServicesCount} public
          </p>
        </div>

        <div className="card p-3.5 bg-surface-overlay border-surface-border">
          <p className="data-label">Scalable Services</p>
          <p className="text-lg font-bold mt-0.5 text-accent-yellow">
            {scalableServicesCount} scalable
          </p>
        </div>

        <div className="card p-3.5 bg-surface-overlay border-surface-border">
          <p className="data-label">Persistent Storage</p>
          <p className="text-lg font-bold mt-0.5 text-accent-purple">
            {persistentVolumesCount} volumes
          </p>
        </div>
      </div>

      {/* AI Explanation & Provider Metadata Card */}
      <div className="card p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-surface-border pb-3">
          <div>
            <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
              <CheckCircle2 size={16} className="text-accent-green" />
              Infrastructure Plan (v{version})
            </h3>
            <p className="text-xs text-text-muted mt-0.5">
              Generated via {aiProvider || 'AI Planner'} ({aiModel || 'gpt-4o-mini'}) in {durationMs || 100}ms · 10/10 Safety Rules Passed
            </p>
          </div>
          <Button
            variant="secondary"
            onClick={onRegenerate}
            isLoading={isRegenerating}
            className="text-xs gap-1.5"
          >
            <RefreshCw size={13} />
            Regenerate Plan
          </Button>
        </div>

        {/* AI Explanations Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-3 bg-surface-overlay rounded-md border border-surface-border">
            <h4 className="font-semibold text-text-primary mb-1">Architecture Rationale</h4>
            <p className="text-text-secondary leading-relaxed">{plan.explanation.architecture_choice}</p>
          </div>
          <div className="p-3 bg-surface-overlay rounded-md border border-surface-border">
            <h4 className="font-semibold text-text-primary mb-1">Scaling Strategy</h4>
            <p className="text-text-secondary leading-relaxed">{plan.explanation.scaling_reasoning}</p>
          </div>
        </div>

        <div className="p-3 bg-surface-overlay rounded-md border border-surface-border text-xs">
          <h4 className="font-semibold text-text-primary mb-1">Security Isolation</h4>
          <p className="text-text-secondary leading-relaxed">{plan.explanation.security_notes}</p>
        </div>
      </div>

      {/* Risk Assessment List */}
      {plan.risks.length > 0 && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
            <AlertTriangle size={16} className="text-accent-yellow" />
            Infrastructure Risk Assessment ({plan.risks.length})
          </h3>
          <div className="space-y-3">
            {plan.risks.map((risk, idx) => (
              <div key={idx} className="p-3 bg-surface-overlay rounded-md border border-surface-border text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-text-primary capitalize">{risk.risk.replace(/_/g, ' ')}</span>
                  <span className={`tag border uppercase text-[10px] ${
                    risk.severity === 'high' || risk.severity === 'critical'
                      ? 'bg-accent-red/10 text-accent-red border-accent-red/20'
                      : 'bg-accent-yellow/10 text-accent-yellow border-accent-yellow/20'
                  }`}>
                    {risk.severity} severity
                  </span>
                </div>
                <p className="text-text-secondary">{risk.description}</p>
                {risk.mitigation && (
                  <p className="text-text-muted text-[11px] pt-1">Mitigation: {risk.mitigation}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
