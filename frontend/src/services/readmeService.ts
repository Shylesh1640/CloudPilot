import api from './api';

export interface ReadmeResponse {
  analysis_id: string;
  content: string;
}

export const readmeService = {
  generate: async (analysisId: string): Promise<ReadmeResponse> => {
    const res = await api.post<ReadmeResponse>(
      `/api/v1/repository-analyses/${analysisId}/readme`
    );
    return res.data;
  },
};
