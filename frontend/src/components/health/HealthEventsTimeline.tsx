import { Activity, AlertTriangle, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import type { HealthEvent } from '@/types';

interface Props {
  events: HealthEvent[];
}

export function HealthEventsTimeline({ events }: Props) {
  if (!events || events.length === 0) {
    return (
      <div className="card p-6 text-center text-xs text-text-muted">
        No health state transition events recorded yet.
      </div>
    );
  }

  const getIcon = (eventType: string) => {
    if (eventType.includes('HEALTHY') || eventType.includes('RECOVERED')) {
      return <CheckCircle size={14} className="text-accent-green" />;
    } else if (eventType.includes('DEGRADED') || eventType.includes('FLAPPING')) {
      return <AlertTriangle size={14} className="text-accent-yellow" />;
    } else {
      return <XCircle size={14} className="text-accent-red" />;
    }
  };

  return (
    <div className="card p-5 border-surface-border space-y-3">
      <div className="flex items-center gap-2 mb-2">
        <Activity size={16} className="text-brand-light" />
        <h3 className="text-sm font-bold text-text-primary">Health Transition Events</h3>
      </div>

      <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
        {events.map((evt) => (
          <div
            key={evt.id}
            className="flex items-start gap-3 p-2.5 rounded-md bg-surface-overlay/50 border border-surface-border text-xs"
          >
            <div className="mt-0.5">{getIcon(evt.event_type)}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="font-bold text-text-primary uppercase font-mono text-[11px]">
                  {evt.service_id} · {evt.event_type}
                </span>
                <span className="text-[10px] text-text-muted">
                  {new Date(evt.created_at).toLocaleTimeString()}
                </span>
              </div>
              <p className="text-text-secondary mt-0.5">{evt.message}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
