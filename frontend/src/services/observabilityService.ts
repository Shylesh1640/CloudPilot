import { api } from './api';
import type {
  ContainerMetricsRead,
  DeploymentMetricsRead,
  LogEntriesRead,
  ServiceMetricsRead,
} from '@/types';

export const observabilityService = {
  async getDeploymentMetrics(deploymentId: string): Promise<DeploymentMetricsRead> {
    const res = await api.get<DeploymentMetricsRead>(`/deployments/${deploymentId}/metrics`);
    return res.data;
  },

  async getServiceCurrentMetrics(deploymentId: string, serviceId: string): Promise<ServiceMetricsRead> {
    const res = await api.get<ServiceMetricsRead>(`/deployments/${deploymentId}/services/${serviceId}/metrics/current`);
    return res.data;
  },

  async getServiceMetricsHistory(
    deploymentId: string,
    serviceId: string,
    minutes = 15,
    limit = 200
  ): Promise<ContainerMetricsRead[]> {
    const res = await api.get<ContainerMetricsRead[]>(
      `/deployments/${deploymentId}/services/${serviceId}/metrics?minutes=${minutes}&limit=${limit}`
    );
    return res.data;
  },

  async getContainerLogs(
    deploymentId: string,
    serviceId: string,
    tail = 100,
    level?: string,
    search?: string
  ): Promise<LogEntriesRead> {
    let url = `/deployments/${deploymentId}/services/${serviceId}/logs?tail=${tail}`;
    if (level) url += `&level=${encodeURIComponent(level)}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;

    const res = await api.get<LogEntriesRead>(url);
    return res.data;
  },
};
