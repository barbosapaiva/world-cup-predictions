import api from './client';
import type { League, LeagueCreate, LeagueMember } from './types';

export async function listLeagues(): Promise<League[]> {
  const res = await api.get<League[]>('/leagues');
  return res.data;
}

export async function getLeague(id: string): Promise<League> {
  const res = await api.get<League>(`/leagues/${id}`);
  return res.data;
}

export async function createLeague(data: LeagueCreate): Promise<League> {
  const res = await api.post<League>('/leagues', data);
  return res.data;
}

export async function joinLeagueByCode(inviteCode: string): Promise<LeagueMember> {
  const res = await api.post<LeagueMember>('/leagues/join', {
    invite_code: inviteCode,
  });
  return res.data;
}

export async function listMembers(leagueId: string): Promise<LeagueMember[]> {
  const res = await api.get<LeagueMember[]>(`/leagues/${leagueId}/members`);
  return res.data;
}
