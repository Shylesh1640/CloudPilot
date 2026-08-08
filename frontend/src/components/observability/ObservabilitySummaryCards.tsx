import { Cpu, HardDrive, Wifi, RefreshCw, Radio } from 'lucide-react';
import type { DeploymentMetricsRead } from '@/types';

interface Props {
  metrics: DeploymentMetricsRead | null;
  socketStatus: 'CONNECTING' | 'LIVE' | 'FALLBACK';
}

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

export function ObservabilitySummaryCards({ metrics, socketStatus }: Props) {
  const isLive = socketStatus === 'LIVE';

  return (
    <div className="space-y-4">
      {/* Live Stream Header Badge */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-bold text-text-primary">Real-Time Telemetry Stream (Phase 6)</h2>
          <span
            className={`tag border text-xs font-semibold flex items-center gap-1.5 ${
              isLive
                ? 'bg-accent-green/10 text-accent-green border-accent-green/30'
                : 'bg-accent-yellow/10 text-accent-yellow border-accent-yellow/30'
            }`}
          >
            <Radio size={12} className={isLive ? 'animate-pulse text-accent-green' : ''} />
            {isLive ? 'LIVE WEBSOCKET' : 'REST POLLING FALLBACK'}
          </span>
        </div>
        <span className="text-xs font-mono text-text-muted">Interval: 5 sec</span>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* CPU % Card */}
        <div className="card p-4 border-surface-border bg-surface-overlay/50 space-y-2">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-xs font-medium">Deployment CPU Load</span>
            <Cpu size={16} className="text-brand-light" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-text-primary">
              {metrics ? `${metrics.avg_cpu_percent}%` : '0.0%'}
            </span>
            <span className="text-xs text-text-muted font-mono">
              Total: {metrics ? `${metrics.total_cpu_percent}%` : '0%'}
            </span>
          </div>
          <div className="w-full bg-surface-base h-1.5 rounded-full overflow-hidden border border-surface-border">
            <div
              className="bg-brand h-full transition-all duration-300"
              style={{ width: `${Math.min(100, metrics?.avg_cpu_percent || 0)}%` }}
            />
          </div>
        </div>

        {/* Memory Card */}
        <div className="card p-4 border-surface-border bg-surface-overlay/50 space-y-2">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-xs font-medium">Memory Usage</span>
            <HardDrive size={16} className="text-accent-blue" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-text-primary">
              {metrics ? formatBytes(metrics.total_memory_usage_bytes) : '0 MB'}
            </span>
            <span className="text-xs text-text-muted font-mono">
              Avg: {metrics ? `${metrics.avg_memory_percent}%` : '0%'}
            </span>
          </div>
          <div className="w-full bg-surface-base h-1.5 rounded-full overflow-hidden border border-surface-border">
            <div
              className="bg-accent-blue h-full transition-all duration-300"
              style={{ width: `${Math.min(100, metrics?.avg_memory_percent || 0)}%` }}
            />
          </div>
        </div>

        {/* Network Rate Card */}
        <div className="card p-4 border-surface-border bg-surface-overlay/50 space-y-2">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-xs font-medium">Network Traffic Rate</span>
            <Wifi size={16} className="text-accent-green" />
          </div>
          <div className="space-y-0.5 font-mono">
            <div className="flex justify-between text-xs">
              <span className="text-text-muted">RX (In):</span>
              <span className="font-semibold text-accent-green">
                {metrics ? `${formatBytes(metrics.total_network_rx_rate)}/s` : '0 B/s'}
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-text-muted">TX (Out):</span>
              <span className="font-semibold text-brand-light">
                {metrics ? `${formatBytes(metrics.total_network_tx_rate)}/s` : '0 B/s'}
              </span>
            </div>
          </div>
        </div>

        {/* Restarts Card */}
        <div className="card p-4 border-surface-border bg-surface-overlay/50 space-y-2">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-xs font-medium">Container Restarts</span>
            <RefreshCw size={16} className="text-accent-yellow" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-text-primary">
              {metrics ? metrics.total_restarts : 0}
            </span>
            <span className="text-xs text-text-muted">Restarts across services</span>
          </div>
        </div>
      </div>
    </div>
  );
}
