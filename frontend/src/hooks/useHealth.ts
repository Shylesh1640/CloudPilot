import { useCallback, useEffect, useState } from 'react';
import { healthService } from '@/services/healthService';
import { getErrorMessage } from '@/services/api';
import type {
  DeploymentHealthRead,
  HealthEvent,
  ServiceHealthRead,
} from '@/types';

export function useHealth(deploymentId: string | null) {
  const [health, setHealth] = useState<DeploymentHealthRead | null>(null);
  const [events, setEvents] = useState<HealthEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchHealth = useCallback(async () => {
    if (!deploymentId) return;
    try {
      const data = await healthService.getDeploymentHealth(deploymentId);
      setHealth(data);
      const evts = await healthService.getDeploymentEvents(deploymentId);
      setEvents(evts);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }, [deploymentId]);

  useEffect(() => {
    if (!deploymentId) return;
    setIsLoading(true);
    fetchHealth().finally(() => setIsLoading(false));

    // Poll every 5 seconds
    const interval = setInterval(fetchHealth, 5000);
    return () => clearInterval(interval);
  }, [deploymentId, fetchHealth]);

  return {
    health,
    events,
    isLoading,
    error,
    refreshHealth: fetchHealth,
  };
}
