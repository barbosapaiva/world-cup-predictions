// --- Auth ---
export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserCreate {
  name: string;
  email: string;
  password: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  is_superadmin: boolean;
  is_active: boolean;
  created_at: string;
}

// --- Leagues ---
export interface LeagueCreate {
  name: string;
  rules?: string;
  season: string;
}

export interface League {
  id: string;
  name: string;
  rules: string | null;
  season: string;
  created_by: string;
  created_at: string;
}

export interface LeagueMember {
  id: string;
  user_id: string;
  league_id: string;
  role: 'admin' | 'participant';
  joined_at: string;
  is_active: boolean;
}

// --- Tournament ---
export type MatchStage = 'group' | 'R32' | 'R16' | 'QF' | 'SF' | '3rd' | 'F';
export type MatchStatus = 'locked' | 'scheduled' | 'live' | 'finished';

export interface Team {
  id: string;
  name: string;
  code: string;
  flag_url: string | null;
  group_letter: string | null;
  confederation: string | null;
}

export interface Match {
  id: string;
  home_team_id: string | null;
  away_team_id: string | null;
  home_placeholder: string | null;
  away_placeholder: string | null;
  stage: MatchStage;
  group_letter: string | null;
  match_number: number;
  match_date: string;
  venue: string | null;
  status: MatchStatus;
  submission_deadline: string;
  home_score: number | null;
  away_score: number | null;
  advancing_team_id: string | null;
}

// --- Predictions ---
export interface PredictionCreate {
  league_id: string;
  match_id: string;
  home_score: number;
  away_score: number;
  advancing_team_id?: string;
}

export interface Prediction {
  id: string;
  user_id: string;
  league_id: string;
  match_id: string;
  home_score: number;
  away_score: number;
  advancing_team_id: string | null;
  submitted_at: string;
  updated_at: string;
}

// --- Rankings ---
export interface RankingEntry {
  position: number;
  user_id: string;
  name: string;
  total_points: number;
  match_points: number;
  special_prediction_points: number;
  exact_scores: number;
  outcome_hits: number;
  group_position_points: number;
}
