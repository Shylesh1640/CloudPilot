import { api } from '@/services/api';
import type { ScalingDecisionRead, ScalingEventRead, ScalingPolicyRead, TrafficRunRead, TrafficScenario } from '@/types';

export interface PolicyPayload {
  enabled: boolean; min_replicas: number; max_replicas: number; target_cpu: number | null;
  target_memory?: number | null; target_request_rate?: number | null; target_latency?: number | null;
  scale_up_cooldown: number; scale_down_cooldown: number; stabilization_window: number;
  max_scale_up_step: number; max_scale_down_step: number; dry_run: boolean; simulation_mode: boolean;
}

export const autoscalingService = {
  async getPolicy(deploymentId: string, serviceId: string) {
    return (await api.get<ScalingPolicyRead>(`/api/v1/deployments/${deploymentId}/services/${serviceId}/scaling`)).data;
  },
  async savePolicy(deploymentId: string, serviceId: string, payload: PolicyPayload) {
    return (await api.put<ScalingPolicyRead>(`/api/v1/deployments/${deploymentId}/services/${serviceId}/scaling`, payload)).data;
  },
  async toggle(deploymentId: string, serviceId: string, enabled: boolean) {
    return (await api.post<ScalingPolicyRead>(`/api/v1/deployments/${deploymentId}/services/${serviceId}/scaling/toggle`, { enabled })).data;
  },
  async scale(deploymentId: string, serviceId: string, replicas: number, dryRun = false) {
    return (await api.post(`/api/v1/deployments/${deploymentId}/services/${serviceId}/scale`, { replicas, dry_run: dryRun })).data;
  },
  async decisions(deploymentId: string) { return (await api.get<ScalingDecisionRead[]>(`/api/v1/deployments/${deploymentId}/scaling/decisions`)).data; },
  async events(deploymentId: string) { return (await api.get<ScalingEventRead[]>(`/api/v1/deployments/${deploymentId}/scaling/events`)).data; },
  async startTraffic(deploymentId: string, payload: { service_id: string; scenario: TrafficScenario; requests_per_second?: number; start_rps?: number; end_rps?: number; duration_seconds: number }) {
    return (await api.post<TrafficRunRead>(`/api/v1/deployments/${deploymentId}/traffic`, payload)).data;
  },
  async traffic(deploymentId: string) { return (await api.get<TrafficRunRead[]>(`/api/v1/deployments/${deploymentId}/traffic`)).data; },
  async stopTraffic(runId: string) { return (await api.post<TrafficRunRead>(`/api/v1/traffic/${runId}/stop`)).data; },
};
