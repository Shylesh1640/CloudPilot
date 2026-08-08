import { useEffect, useState } from 'react';
import { X, Terminal, RefreshCw, Copy, Check } from 'lucide-react';
import { deploymentService } from '@/services/deploymentService';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface Props {
  deploymentId: string;
  serviceId: string;
  serviceName: string;
  onClose: () => void;
}

export function ServiceLogsModal({ deploymentId, serviceId, serviceName, onClose }: Props) {
  const [logs, setLogs] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const data = await deploymentService.getLogs(deploymentId, serviceId, 200);
      setLogs(data.logs || 'No log output returned from container.');
    } catch (err) {
      setLogs('Failed to retrieve container logs.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [deploymentId, serviceId]);

  const handleCopy = () => {
    navigator.clipboard.writeText(logs);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4 backdrop-blur-xs animate-fade-in">
      <div className="card w-full max-w-3xl bg-surface-base border-surface-border shadow-2xl flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-4 border-b border-surface-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal size={16} className="text-brand-light" />
            <div>
              <h3 className="text-sm font-bold text-text-primary">Container Logs: {serviceName}</h3>
              <p className="text-[11px] font-mono text-text-muted">service_id: {serviceId}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="p-1.5 text-text-muted hover:text-text-primary rounded hover:bg-surface-overlay transition-colors flex items-center gap-1 text-xs"
              title="Copy Logs"
            >
              {copied ? <Check size={14} className="text-accent-green" /> : <Copy size={14} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            <button
              onClick={fetchLogs}
              className="p-1.5 text-text-muted hover:text-text-primary rounded hover:bg-surface-overlay transition-colors"
              title="Refresh Logs"
            >
              <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
            </button>

            <button
              onClick={onClose}
              className="p-1.5 text-text-muted hover:text-text-primary rounded hover:bg-surface-overlay transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Terminal Window */}
        <div className="p-4 flex-1 bg-black overflow-y-auto font-mono text-xs text-text-secondary leading-relaxed space-y-1 rounded-b-lg select-text">
          {isLoading ? (
            <div className="flex justify-center py-10">
              <LoadingSpinner />
            </div>
          ) : (
            <pre className="whitespace-pre-wrap font-mono text-xs text-green-400">{logs}</pre>
          )}
        </div>
      </div>
    </div>
  );
}
