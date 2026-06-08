import api from './client';
import type { RankingEntry } from './types';

export async function getLeagueRanking(leagueId: string): Promise<RankingEntry[]> {
  const res = await api.get<RankingEntry[]>(`/rankings/leagues/${leagueId}`);
  return res.data;
}
