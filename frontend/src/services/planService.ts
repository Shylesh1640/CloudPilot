import { api } from '@/services/api';
import type { PlanRead, PlanResultRead } from '@/types';

export const planService = {
  /** Trigger AI infrastructure planning for a completed repository analysis */
  async generatePlan(analysisId: string): Promise<PlanRead> {
    const res = await api.post<PlanRead>(`/api/v1/repository-analyses/${analysisId}/plan`);
    return res.data;
  },

  /** Get infrastructure plan generation status */
  async getStatus(planId: string): Promise<PlanRead> {
    const res = await api.get<PlanRead>(`/api/v1/infrastructure-plans/${planId}`);
    return res.data;
  },

  /** Get full validated infrastructure plan result */
  async getResult(planId: string): Promise<PlanResultRead> {
    const res = await api.get<PlanResultRead>(`/api/v1/infrastructure-plans/${planId}/result`);
    return res.data;
  },

  /** Trigger new plan version regeneration */
  async regeneratePlan(planId: string): Promise<PlanRead> {
    const res = await api.post<PlanRead>(`/api/v1/infrastructure-plans/${planId}/regenerate`);
    return res.data;
  },
};
