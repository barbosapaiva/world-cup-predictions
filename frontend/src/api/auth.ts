import api from './client';
import type { LoginRequest, TokenResponse, User, UserCreate } from './types';

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const res = await api.post<TokenResponse>('/auth/login', data);
  return res.data;
}

export async function register(data: UserCreate): Promise<User> {
  const res = await api.post<User>('/auth/register', data);
  return res.data;
}

export async function getMe(): Promise<User> {
  const res = await api.get<User>('/auth/me');
  return res.data;
}
