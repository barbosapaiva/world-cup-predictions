import api from './client';
import type { SpecialPrediction, SpecialPredictionCreate } from './types';

export async function submitSpecialPrediction(data: SpecialPredictionCreate): Promise<SpecialPrediction> {
  const res = await api.post<SpecialPrediction>('/special-predictions', data);
  return res.data;
}

export async function listMySpecialPredictions(leagueId: string): Promise<SpecialPrediction[]> {
  const res = await api.get<SpecialPrediction[]>('/special-predictions/me', {
    params: { league_id: leagueId },
  });
  return res.data;
}

export async function listLeagueSpecialPredictions(leagueId: string): Promise<SpecialPrediction[]> {
  const res = await api.get<SpecialPrediction[]>(`/special-predictions/league/${leagueId}`);
  return res.data;
}
