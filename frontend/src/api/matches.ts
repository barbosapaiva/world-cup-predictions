import api from './client';
import type { Match, Team } from './types';

export async function listMatches(): Promise<Match[]> {
  const res = await api.get<Match[]>('/tournament/matches');
  return res.data;
}

export async function getMatch(id: string): Promise<Match> {
  const res = await api.get<Match>(`/tournament/matches/${id}`);
  return res.data;
}

export async function listTeams(): Promise<Team[]> {
  const res = await api.get<Team[]>('/tournament/teams');
  return res.data;
}
