import { api } from './api';
import type {
  DeploymentHealthRead,
  HealthCheckRecord,
  HealthEvent,
  ServiceHealthRead,
} from '@/types';

export const healthService = {
  async getDeploymentHealth(deploymentId: string): Promise<DeploymentHealthRead> {
    const res = await api.get<DeploymentHealthRead>(`/deployments/${deploymentId}/health`);
    return res.data;
  },

  async getServiceHealth(deploymentId: string, serviceId: string): Promise<ServiceHealthRead> {
    const res = await api.get<ServiceHealthRead>(`/deployments/${deploymentId}/services/${serviceId}/health`);
    return res.data;
  },

  async getServiceHealthHistory(deploymentId: string, serviceId: string, limit = 100): Promise<HealthCheckRecord[]> {
    const res = await api.get<HealthCheckRecord[]>(
      `/deployments/${deploymentId}/services/${serviceId}/health/history?limit=${limit}`
    );
    return res.data;
  },

  async getDeploymentEvents(deploymentId: string, limit = 50): Promise<HealthEvent[]> {
    const res = await api.get<HealthEvent[]>(`/deployments/${deploymentId}/health/events?limit=${limit}`);
    return res.data;
  },
};
