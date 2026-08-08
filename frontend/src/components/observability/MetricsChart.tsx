import { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { observabilityService } from '@/services/observabilityService';
import type { ContainerMetricsRead } from '@/types';

interface Props {
  deploymentId: string;
  serviceId: string;
}

export function MetricsChart({ deploymentId, serviceId }: Props) {
  const [range, setRange] = useState<number>(15); // minutes
  const [history, setHistory] = useState<ContainerMetricsRead[]>([]);
  const [metricType, setMetricType] = useState<'cpu' | 'memory' | 'network'>('cpu');

  useEffect(() => {
    let isMounted = true;
    observabilityService
      .getServiceMetricsHistory(deploymentId, serviceId, range)
      .then((data) => {
        if (isMounted) setHistory(data);
      })
      .catch(() => {});

    return () => {
      isMounted = false;
    };
  }, [deploymentId, serviceId, range]);

  const chartData = history.map((h) => ({
    time: new Date(h.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    cpu: h.cpu_percent,
    memory: h.memory_percent,
    rxRate: Math.round(h.network_rx_rate / 1024), // KB/s
    txRate: Math.round(h.network_tx_rate / 1024), // KB/s
  }));

  return (
    <div className="card p-5 border-surface-border space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-surface-border pb-3">
        <div>
          <h3 className="text-sm font-bold text-text-primary capitalize">
            {serviceId} Telemetry Chart
          </h3>
          <p className="text-xs text-text-muted">Time-series history</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Metric Selector */}
          <div className="flex bg-surface-overlay p-0.5 rounded border border-surface-border text-xs font-medium">
            <button
              onClick={() => setMetricType('cpu')}
              className={`px-2.5 py-1 rounded transition-colors ${
                metricType === 'cpu' ? 'bg-brand text-white font-bold' : 'text-text-muted hover:text-text-primary'
              }`}
            >
              CPU %
            </button>
            <button
              onClick={() => setMetricType('memory')}
              className={`px-2.5 py-1 rounded transition-colors ${
                metricType === 'memory' ? 'bg-brand text-white font-bold' : 'text-text-muted hover:text-text-primary'
              }`}
            >
              Memory %
            </button>
            <button
              onClick={() => setMetricType('network')}
              className={`px-2.5 py-1 rounded transition-colors ${
                metricType === 'network' ? 'bg-brand text-white font-bold' : 'text-text-muted hover:text-text-primary'
              }`}
            >
              Network KB/s
            </button>
          </div>

          {/* Time Range Selector */}
          <div className="flex bg-surface-overlay p-0.5 rounded border border-surface-border text-xs font-mono">
            {[5, 15, 30, 60].map((m) => (
              <button
                key={m}
                onClick={() => setRange(m)}
                className={`px-2 py-1 rounded transition-colors ${
                  range === m ? 'bg-surface-border text-text-primary font-bold' : 'text-text-muted hover:text-text-primary'
                }`}
              >
                {m}m
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-56 w-full pt-2">
        {chartData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-text-muted">
            Collecting time-series metrics...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorMetric" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--brand, #6366f1)" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="var(--brand, #6366f1)" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '6px',
                  fontSize: '12px',
                }}
              />
              <Area
                type="monotone"
                dataKey={metricType === 'cpu' ? 'cpu' : metricType === 'memory' ? 'memory' : 'rxRate'}
                stroke="#6366f1"
                fillOpacity={1}
                fill="url(#colorMetric)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
