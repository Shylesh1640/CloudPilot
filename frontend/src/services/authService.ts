import api from './api';
import type { LoginPayload, RegisterPayload, TokenResponse, User } from '@/types';

export const authService = {
  register: async (payload: RegisterPayload): Promise<User> => {
    const { data } = await api.post<User>('/api/v1/auth/register', payload);
    return data;
  },

  login: async (payload: LoginPayload): Promise<TokenResponse> => {
    const { data } = await api.post<TokenResponse>('/api/v1/auth/login', payload);
    return data;
  },

  me: async (): Promise<User> => {
    const { data } = await api.get<User>('/api/v1/auth/me');
    return data;
  },
};
