import { api } from '@/services/api';
import type { RepositoryAnalysis } from '@/types';

export const analysisService = {
  /** Trigger background analysis of a public GitHub repository */
  async analyze(projectId: string, repositoryUrl: string): Promise<RepositoryAnalysis> {
    const res = await api.post<RepositoryAnalysis>(
      `/api/v1/projects/${projectId}/repositories/analyze`,
      { repository_url: repositoryUrl }
    );
    return res.data;
  },

  /** Get analysis status and progress percentage */
  async getStatus(analysisId: string): Promise<RepositoryAnalysis> {
    const res = await api.get<RepositoryAnalysis>(`/api/v1/repository-analyses/${analysisId}`);
    return res.data;
  },

  /** Get complete repository profile result */
  async getResult(analysisId: string): Promise<RepositoryAnalysis> {
    const res = await api.get<RepositoryAnalysis>(`/api/v1/repository-analyses/${analysisId}/result`);
    return res.data;
  },
};
