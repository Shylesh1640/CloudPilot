import { useCallback, useEffect, useRef, useState } from 'react';
import { observabilityService } from '@/services/observabilityService';
import type { DeploymentMetricsRead } from '@/types';

export function useObservabilitySocket(deploymentId: string | null) {
  const [metrics, setMetrics] = useState<DeploymentMetricsRead | null>(null);
  const [socketStatus, setSocketStatus] = useState<'CONNECTING' | 'LIVE' | 'FALLBACK'>('CONNECTING');
  const [error, setError] = useState('');
  const wsRef = useRef<WebSocket | null>(null);

  const fetchRest = useCallback(async () => {
    if (!deploymentId) return;
    try {
      const data = await observabilityService.getDeploymentMetrics(deploymentId);
      setMetrics(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch REST metrics');
    }
  }, [deploymentId]);

  useEffect(() => {
    if (!deploymentId) return;

    // Fetch initial state via REST
    fetchRest();

    const token = localStorage.getItem('token') || '';
    if (!token) {
      setSocketStatus('FALLBACK');
      const pollInterval = setInterval(fetchRest, 5000);
      return () => clearInterval(pollInterval);
    }

    const wsUrl = `ws://${window.location.host}/ws/deployments/${deploymentId}?token=${encodeURIComponent(token)}`;
    let ws: WebSocket;

    try {
      ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setSocketStatus('LIVE');
      };

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          if (parsed.type === 'metrics.update' && parsed.data) {
            fetchRest(); // Refresh aggregated state
          }
        } catch {}
      };

      ws.onerror = () => {
        setSocketStatus('FALLBACK');
      };

      ws.onclose = () => {
        setSocketStatus('FALLBACK');
      };
    } catch {
      setSocketStatus('FALLBACK');
    }

    // Polling fallback
    const interval = setInterval(() => {
      fetchRest();
    }, 5000);

    return () => {
      clearInterval(interval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [deploymentId, fetchRest]);

  return {
    metrics,
    socketStatus,
    error,
    refreshMetrics: fetchRest,
  };
}
