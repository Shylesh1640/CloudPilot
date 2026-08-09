import { api } from '@/services/api';
import type { FailureInjectionRead, FailureScenario, IncidentAIAnalysis, IncidentRead, RecoveryAttemptRead, RecoveryEventRead } from '@/types';

export const reliabilityService = {
  async inject(deploymentId: string, payload: { service_id: string; scenario: FailureScenario; replica_id?: number; duration_seconds: number; simulation: boolean }) { return (await api.post<FailureInjectionRead>(`/api/v1/deployments/${deploymentId}/failure-injections`, payload)).data; },
  async incidents(deploymentId: string) { return (await api.get<IncidentRead[]>(`/api/v1/deployments/${deploymentId}/incidents`)).data; },
  async timeline(incidentId: string) { return (await api.get<RecoveryEventRead[]>(`/api/v1/incidents/${incidentId}/timeline`)).data; },
  async recovery(incidentId: string) { return (await api.get<RecoveryAttemptRead[]>(`/api/v1/incidents/${incidentId}/recovery`)).data; },
  async recover(incidentId: string, dryRun = false) { return (await api.post(`/api/v1/incidents/${incidentId}/recover`, { dry_run: dryRun })).data; },
  async aiAnalysis(incidentId: string, refresh = false) { return (await (refresh ? api.post<IncidentAIAnalysis>(`/api/v1/incidents/${incidentId}/ai-analysis`) : api.get<IncidentAIAnalysis>(`/api/v1/incidents/${incidentId}/ai-analysis`))).data; },
  async askIncident(incidentId: string, question: string) { return (await api.post<{ answer: string }>(`/api/v1/incidents/${incidentId}/assistant`, { question })).data; },
};
