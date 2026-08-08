import api from './api';
import type { CreateProjectPayload, Project, UpdateProjectPayload } from '@/types';

export const projectService = {
  list: async (): Promise<Project[]> => {
    const { data } = await api.get<Project[]>('/api/v1/projects');
    return data;
  },

  get: async (id: string): Promise<Project> => {
    const { data } = await api.get<Project>(`/api/v1/projects/${id}`);
    return data;
  },

  create: async (payload: CreateProjectPayload): Promise<Project> => {
    const { data } = await api.post<Project>('/api/v1/projects', payload);
    return data;
  },

  update: async (id: string, payload: UpdateProjectPayload): Promise<Project> => {
    const { data } = await api.put<Project>(`/api/v1/projects/${id}`, payload);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/v1/projects/${id}`);
  },
};
