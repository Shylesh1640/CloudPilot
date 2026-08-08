import { useCallback, useEffect, useRef, useState } from 'react';
import { deploymentService } from '@/services/deploymentService';
import type { DeploymentRead, DeploymentServiceInfo } from '@/types';

export function useDeployment(initialDeploymentId?: string | null) {
  const [deploymentId, setDeploymentId] = useState<string | null>(initialDeploymentId ?? null);
  const [deployment, setDeployment] = useState<DeploymentRead | null>(null);
  const [services, setServices] = useState<DeploymentServiceInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const stopPolling = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const pollStatus = useCallback(async (id: string) => {
    try {
      const data = await deploymentService.getStatus(id);
      setDeployment(data);
      if (data.services && data.services.length > 0) {
        setServices(data.services);
      }

      if (['RUNNING', 'FAILED', 'STOPPED'].includes(data.status)) {
        stopPolling();
        setIsLoading(false);
        if (data.status === 'FAILED') {
          setError(data.error_message || 'Container deployment failed.');
        }
      }
    } catch (err) {
      console.error('Error polling deployment status:', err);
    }
  }, [stopPolling]);

  useEffect(() => {
    if (!deploymentId) return;

    pollStatus(deploymentId);
    timerRef.current = setInterval(() => {
      pollStatus(deploymentId);
    }, 2000);

    return () => stopPolling();
  }, [deploymentId, pollStatus, stopPolling]);

  const triggerDeployment = useCallback(async (planId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const newDeployment = await deploymentService.triggerDeployment(planId);
      setDeploymentId(newDeployment.id);
      setDeployment(newDeployment);
      return newDeployment;
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to start container deployment.';
      setError(msg);
      setIsLoading(false);
      throw err;
    }
  }, []);

  const stopDeployment = useCallback(async () => {
    if (!deploymentId) return;
    try {
      const updated = await deploymentService.stopDeployment(deploymentId);
      setDeployment(updated);
    } catch (err: any) {
      console.error('Error stopping deployment:', err);
    }
  }, [deploymentId]);

  const restartService = useCallback(async (serviceId: string) => {
    if (!deploymentId) return;
    try {
      await deploymentService.restartService(deploymentId, serviceId);
      await pollStatus(deploymentId);
    } catch (err: any) {
      console.error(`Error restarting service ${serviceId}:`, err);
    }
  }, [deploymentId, pollStatus]);

  return {
    deploymentId,
    deployment,
    services,
    isLoading,
    error,
    triggerDeployment,
    stopDeployment,
    restartService,
    setDeploymentId,
  };
}
