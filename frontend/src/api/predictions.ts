import api from './client';
import type { Prediction, PredictionCreate } from './types';

export async function createPrediction(data: PredictionCreate): Promise<Prediction> {
  const res = await api.post<Prediction>('/predictions', data);
  return res.data;
}

export async function updatePrediction(
  id: string,
  data: { home_score?: number; away_score?: number; advancing_team_id?: string | null }
): Promise<Prediction> {
  const res = await api.patch<Prediction>(`/predictions/${id}`, data);
  return res.data;
}

export async function listMyPredictions(leagueId?: string): Promise<Prediction[]> {
  const params = leagueId ? { league_id: leagueId } : {};
  const res = await api.get<Prediction[]>('/predictions/me', { params });
  return res.data;
}

export async function listMatchPredictions(matchId: string, leagueId: string): Promise<Prediction[]> {
  const res = await api.get<Prediction[]>(`/predictions/matches/${matchId}`, { params: { league_id: leagueId } });
  return res.data;
}
