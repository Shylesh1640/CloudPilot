import { useCallback, useEffect, useRef, useState } from 'react';
import { planService } from '@/services/planService';
import type { PlanResultRead } from '@/types';

export function usePlan(initialPlanId?: string | null) {
  const [planId, setPlanId] = useState<string | null>(initialPlanId ?? null);
  const [planResult, setPlanResult] = useState<PlanResultRead | null>(null);
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
      const data = await planService.getStatus(id);

      if (data.status === 'COMPLETED') {
        stopPolling();
        const fullResult = await planService.getResult(id);
        setPlanResult(fullResult);
        setIsLoading(false);
      } else if (data.status === 'FAILED') {
        stopPolling();
        setError(data.error_message || 'Infrastructure plan generation failed.');
        setIsLoading(false);
      }
    } catch (err) {
      console.error('Error polling plan status:', err);
    }
  }, [stopPolling]);

  useEffect(() => {
    if (!planId) return;

    pollStatus(planId);
    timerRef.current = setInterval(() => {
      pollStatus(planId);
    }, 2000);

    return () => stopPolling();
  }, [planId, pollStatus, stopPolling]);

  const generatePlan = useCallback(async (analysisId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const newPlan = await planService.generatePlan(analysisId);
      setPlanId(newPlan.id);
      return newPlan;
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to start AI infrastructure planning.';
      setError(msg);
      setIsLoading(false);
      throw err;
    }
  }, []);

  const regeneratePlan = useCallback(async (currentPlanId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const newPlan = await planService.regeneratePlan(currentPlanId);
      setPlanId(newPlan.id);
      return newPlan;
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to regenerate plan.';
      setError(msg);
      setIsLoading(false);
      throw err;
    }
  }, []);

  return {
    planId,
    planResult,
    isLoading,
    error,
    generatePlan,
    regeneratePlan,
    setPlanId,
  };
}
