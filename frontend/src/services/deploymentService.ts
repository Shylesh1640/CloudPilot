import { api } from '@/services/api';
import type { DeploymentRead, DeploymentServiceInfo, ServiceLogsRead } from '@/types';

export const deploymentService = {
  /** Trigger container deployment from a validated infrastructure plan */
  async triggerDeployment(planId: string): Promise<DeploymentRead> {
    const res = await api.post<DeploymentRead>(`/api/v1/infrastructure-plans/${planId}/deploy`);
    return res.data;
  },

  /** Get deployment status and timeline progress */
  async getStatus(deploymentId: string): Promise<DeploymentRead> {
    const res = await api.get<DeploymentRead>(`/api/v1/deployments/${deploymentId}`);
    return res.data;
  },

  /** Get deployment services list with desired vs actual states */
  async getServices(deploymentId: string): Promise<DeploymentServiceInfo[]> {
    const res = await api.get<DeploymentServiceInfo[]>(`/api/v1/deployments/${deploymentId}/services`);
    return res.data;
  },

  /** Stop deployment containers */
  async stopDeployment(deploymentId: string): Promise<DeploymentRead> {
    const res = await api.post<DeploymentRead>(`/api/v1/deployments/${deploymentId}/stop`);
    return res.data;
  },

  /** Restart a specific service container */
  async restartService(deploymentId: string, serviceId: string): Promise<void> {
    await api.post(`/api/v1/deployments/${deploymentId}/services/${serviceId}/restart`);
  },

  /** Get service container logs */
  async getLogs(deploymentId: string, serviceId: string, limit: number = 200): Promise<ServiceLogsRead> {
    const res = await api.get<ServiceLogsRead>(
      `/api/v1/deployments/${deploymentId}/services/${serviceId}/logs?limit=${limit}`
    );
    return res.data;
  },
};
