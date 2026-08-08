import { useCallback, useEffect, useRef, useState } from 'react';
import { analysisService } from '@/services/analysisService';
import type { RepositoryAnalysis } from '@/types';

export function useAnalysis(initialAnalysisId?: string | null) {
  const [analysisId, setAnalysisId] = useState<string | null>(initialAnalysisId ?? null);
  const [analysis, setAnalysis] = useState<RepositoryAnalysis | null>(null);
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
      const data = await analysisService.getStatus(id);
      setAnalysis(data);

      if (data.status === 'COMPLETED') {
        stopPolling();
        // Fetch full profile result
        const fullData = await analysisService.getResult(id);
        setAnalysis(fullData);
      } else if (data.status === 'FAILED') {
        stopPolling();
        setError(data.error_message || 'Repository analysis failed.');
      }
    } catch (err) {
      console.error('Error polling analysis status:', err);
    }
  }, [stopPolling]);

  useEffect(() => {
    if (!analysisId) return;

    // Initial fetch
    pollStatus(analysisId);

    // Setup polling every 2s
    timerRef.current = setInterval(() => {
      pollStatus(analysisId);
    }, 2000);

    return () => stopPolling();
  }, [analysisId, pollStatus, stopPolling]);

  const startAnalysis = useCallback(async (projectId: string, url: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const newAnalysis = await analysisService.analyze(projectId, url);
      setAnalysis(newAnalysis);
      setAnalysisId(newAnalysis.id);
      return newAnalysis;
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.response?.data?.error?.message || 'Failed to start analysis.';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    analysis,
    analysisId,
    isLoading,
    error,
    startAnalysis,
    setAnalysisId,
  };
}
