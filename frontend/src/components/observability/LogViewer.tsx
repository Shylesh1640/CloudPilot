import { useEffect, useState } from 'react';
import { Terminal, Search, Filter, RefreshCw } from 'lucide-react';
import { observabilityService } from '@/services/observabilityService';
import type { LogEntry } from '@/types';

interface Props {
  deploymentId: string;
  serviceId: string;
}

export function LogViewer({ deploymentId, serviceId }: Props) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filterLevel, setFilterLevel] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const data = await observabilityService.getContainerLogs(
        deploymentId,
        serviceId,
        150,
        filterLevel,
        searchTerm
      );
      setLogs(data.lines);
    } catch {}
    setIsLoading(false);
  };

  useEffect(() => {
    fetchLogs();
  }, [deploymentId, serviceId, filterLevel]);

  return (
    <div className="card p-5 border-surface-border space-y-3">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-surface-border pb-3">
        <div className="flex items-center gap-2">
          <Terminal size={16} className="text-brand-light" />
          <h3 className="text-sm font-bold text-text-primary">Container Application Logs</h3>
        </div>

        <div className="flex items-center gap-2">
          {/* Level Filter */}
          <select
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value)}
            className="bg-surface-overlay border border-surface-border text-xs rounded px-2 py-1 text-text-secondary focus:outline-none"
          >
            <option value="ALL">All Levels</option>
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="ERROR">ERROR</option>
          </select>

          {/* Search Input */}
          <div className="relative">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchLogs()}
              placeholder="Search logs..."
              className="bg-surface-overlay border border-surface-border text-xs rounded pl-7 pr-2 py-1 text-text-secondary w-36 focus:outline-none"
            />
            <Search size={12} className="absolute left-2 top-2 text-text-muted" />
          </div>

          <button
            onClick={fetchLogs}
            disabled={isLoading}
            className="p-1.5 bg-surface-overlay hover:bg-surface-border rounded border border-surface-border text-text-muted hover:text-text-primary transition-colors"
            title="Refresh Logs"
          >
            <RefreshCw size={13} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Terminal Monospace Output */}
      <div className="bg-black/90 rounded-md p-4 font-mono text-xs max-h-72 overflow-y-auto border border-surface-border/60 space-y-1">
        {logs.length === 0 ? (
          <p className="text-text-muted italic">No log entries matching criteria.</p>
        ) : (
          logs.map((line, idx) => (
            <div key={idx} className="flex items-start gap-2 leading-relaxed">
              <span className="text-text-muted select-none text-[10px]">
                {new Date(line.timestamp).toLocaleTimeString()}
              </span>
              <span
                className={`font-bold text-[10px] px-1 rounded uppercase ${
                  line.level === 'ERROR'
                    ? 'bg-accent-red/20 text-accent-red'
                    : line.level === 'WARN'
                    ? 'bg-accent-yellow/20 text-accent-yellow'
                    : 'bg-brand/20 text-brand-light'
                }`}
              >
                {line.level}
              </span>
              <span className="text-text-secondary break-all flex-1">{line.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
