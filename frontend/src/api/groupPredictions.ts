import api from './client';
import type { GroupPrediction, GroupPredictionCreate } from './types';

export async function listGroupPredictions(leagueId: string): Promise<GroupPrediction[]> {
  const res = await api.get<GroupPrediction[]>(`/leagues/${leagueId}/group-predictions`);
  return res.data;
}

export async function submitGroupPrediction(
  leagueId: string,
  data: GroupPredictionCreate,
): Promise<GroupPrediction> {
  const res = await api.post<GroupPrediction>(`/leagues/${leagueId}/group-predictions`, data);
  return res.data;
}
