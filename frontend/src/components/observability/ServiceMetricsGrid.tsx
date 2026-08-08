import { Activity, Cpu, HardDrive, Wifi, RefreshCw } from 'lucide-react';
import type { DeploymentMetricsRead, HealthStatus } from '@/types';

interface Props {
  metrics: DeploymentMetricsRead | null;
  healthMap?: Record<string, HealthStatus>;
  selectedServiceId: string | null;
  onSelectService: (serviceId: string) => void;
}

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function ServiceMetricsGrid({ metrics, healthMap, selectedServiceId, onSelectService }: Props) {
  if (!metrics || !metrics.services || Object.keys(metrics.services).length === 0) {
    return (
      <div className="card p-6 text-center text-xs text-text-muted">
        No active service telemetry data.
      </div>
    );
  }

  const services = Object.values(metrics.services);

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-bold text-text-primary">Service Telemetry Matrix</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {services.map((svc) => {
          const isSelected = selectedServiceId === svc.service_id;
          const healthStatus = healthMap?.[svc.service_id];

          return (
            <div
              key={svc.service_id}
              onClick={() => onSelectService(svc.service_id)}
              className={`
                card p-4 border transition-all cursor-pointer space-y-3
                ${isSelected ? 'border-brand ring-1 ring-brand bg-surface-overlay' : 'border-surface-border bg-surface-overlay/30 hover:border-surface-border/80'}
              `}
            >
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-bold text-text-primary uppercase font-mono">
                    {svc.service_id}
                  </h4>
                  <span className="tag bg-surface-border text-text-secondary capitalize text-[10px]">
                    {svc.container_state}
                  </span>
                </div>

                {/* Health Badge */}
                {healthStatus && (
                  <span
                    className={`tag border text-[10px] font-bold ${
                      healthStatus === 'HEALTHY'
                        ? 'bg-accent-green/10 text-accent-green border-accent-green/30'
                        : healthStatus === 'DEGRADED'
                        ? 'bg-accent-yellow/10 text-accent-yellow border-accent-yellow/30'
                        : 'bg-accent-red/10 text-accent-red border-accent-red/30'
                    }`}
                  >
                    ● {healthStatus}
                  </span>
                )}
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 rounded bg-surface-base border border-surface-border/50">
                  <span className="text-[10px] text-text-muted flex items-center gap-1">
                    <Cpu size={10} /> CPU
                  </span>
                  <span className="font-bold text-brand-light mt-0.5 block">{svc.cpu_percent}%</span>
                </div>

                <div className="p-2 rounded bg-surface-base border border-surface-border/50">
                  <span className="text-[10px] text-text-muted flex items-center gap-1">
                    <HardDrive size={10} /> Memory
                  </span>
                  <span className="font-bold text-accent-blue mt-0.5 block">
                    {formatBytes(svc.memory_usage_bytes)} ({svc.memory_percent}%)
                  </span>
                </div>

                <div className="p-2 rounded bg-surface-base border border-surface-border/50">
                  <span className="text-[10px] text-text-muted flex items-center gap-1">
                    <Wifi size={10} /> Net RX/TX
                  </span>
                  <span className="font-bold text-accent-green mt-0.5 block truncate text-[11px]">
                    {formatBytes(svc.network_rx_rate)}/s
                  </span>
                </div>

                <div className="p-2 rounded bg-surface-base border border-surface-border/50">
                  <span className="text-[10px] text-text-muted flex items-center gap-1">
                    <RefreshCw size={10} /> Restarts
                  </span>
                  <span className="font-bold text-text-secondary mt-0.5 block">{svc.restart_count}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
