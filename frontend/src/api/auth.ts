import api from './client';
import type { LoginRequest, User, UserCreate } from './types';

export async function login(data: LoginRequest): Promise<void> {
  await api.post('/auth/login', data);
}

export async function logout(): Promise<void> {
  await api.post('/auth/logout');
}

export async function register(data: UserCreate): Promise<User> {
  const res = await api.post<User>('/auth/register', data);
  return res.data;
}

export async function getMe(): Promise<User> {
  const res = await api.get<User>('/auth/me');
  return res.data;
}
