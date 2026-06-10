import api from './client';
import type { Match, Team, Player } from './types';

export async function listMatches(): Promise<Match[]> {
  const res = await api.get<Match[]>('/matches');
  return res.data;
}

export async function getMatch(id: string): Promise<Match> {
  const res = await api.get<Match>(`/matches/${id}`);
  return res.data;
}

export async function listTeams(): Promise<Team[]> {
  const res = await api.get<Team[]>('/teams');
  return res.data;
}

export async function listPlayers(): Promise<Player[]> {
  const res = await api.get<Player[]>('/players');
  return res.data;
}
