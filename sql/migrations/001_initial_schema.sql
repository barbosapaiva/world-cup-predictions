-- ============================================
-- World Cup Predictions — Initial Schema
-- Migration: 001_initial_schema.sql
-- Database: PostgreSQL 16+
-- All timestamps stored in UTC
-- ============================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- ENUM TYPES
-- ============================================

CREATE TYPE user_role AS ENUM ('admin', 'participant');
CREATE TYPE player_position AS ENUM ('GK', 'DF', 'MF', 'FW');
CREATE TYPE match_stage AS ENUM ('group', 'R32', 'R16', 'QF', 'SF', '3rd', 'F');
CREATE TYPE match_status AS ENUM ('locked', 'scheduled', 'live', 'finished');
CREATE TYPE special_category AS ENUM ('champion', 'mvp', 'golden_boot', 'young_player', 'best_gk');

-- ============================================
-- TABLES
-- ============================================

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_superadmin BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Leagues
CREATE TABLE leagues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    rules TEXT,
    season VARCHAR(20) NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_leagues_created_by ON leagues(created_by);

-- League Members
CREATE TABLE league_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    league_id UUID NOT NULL REFERENCES leagues(id),
    role user_role NOT NULL DEFAULT 'participant',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    UNIQUE (user_id, league_id)
);

CREATE INDEX idx_league_members_user ON league_members(user_id);
CREATE INDEX idx_league_members_league ON league_members(league_id);

-- Teams
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(3) NOT NULL UNIQUE,
    flag_url VARCHAR(500),
    group_letter CHAR(1),
    confederation VARCHAR(20)
);

CREATE INDEX idx_teams_group ON teams(group_letter);

-- Players
CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id),
    name VARCHAR(150) NOT NULL,
    position player_position NOT NULL,
    birth_date DATE
);

CREATE INDEX idx_players_team ON players(team_id);

-- Matches
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    home_team_id UUID REFERENCES teams(id),
    away_team_id UUID REFERENCES teams(id),
    home_placeholder VARCHAR(10),
    away_placeholder VARCHAR(10),
    stage match_stage NOT NULL,
    group_letter CHAR(1),
    match_number INT NOT NULL UNIQUE,
    match_date TIMESTAMPTZ NOT NULL,
    venue VARCHAR(200),
    status match_status NOT NULL DEFAULT 'scheduled',
    submission_deadline TIMESTAMPTZ NOT NULL,
    home_score INT,
    away_score INT,
    advancing_team_id UUID REFERENCES teams(id),

    CONSTRAINT chk_home_team CHECK (home_team_id IS NOT NULL OR home_placeholder IS NOT NULL),
    CONSTRAINT chk_away_team CHECK (away_team_id IS NOT NULL OR away_placeholder IS NOT NULL),

    CONSTRAINT chk_advancing_knockout CHECK (
        advancing_team_id IS NULL OR stage != 'group'
    ),

    CONSTRAINT chk_advancing_valid CHECK (
        advancing_team_id IS NULL
        OR advancing_team_id = home_team_id
        OR advancing_team_id = away_team_id
    ),

    CONSTRAINT chk_scores_pair CHECK (
        (home_score IS NULL AND away_score IS NULL)
        OR (home_score IS NOT NULL AND away_score IS NOT NULL)
    ),

    CONSTRAINT chk_scores_positive CHECK (
        (home_score IS NULL OR home_score >= 0)
        AND (away_score IS NULL OR away_score >= 0)
    ),

    CONSTRAINT chk_submission_deadline_before_match CHECK (
        submission_deadline <= match_date
    )
);

CREATE INDEX idx_matches_stage ON matches(stage);
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_group ON matches(group_letter);
CREATE INDEX idx_matches_home_team ON matches(home_team_id);
CREATE INDEX idx_matches_away_team ON matches(away_team_id);

-- Predictions
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    match_id UUID NOT NULL REFERENCES matches(id),
    league_id UUID NOT NULL REFERENCES leagues(id),
    home_score INT NOT NULL,
    away_score INT NOT NULL,
    advancing_team_id UUID REFERENCES teams(id),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (user_id, match_id, league_id),

    CONSTRAINT chk_pred_scores_positive CHECK (home_score >= 0 AND away_score >= 0)
);

CREATE INDEX idx_predictions_user ON predictions(user_id);
CREATE INDEX idx_predictions_match ON predictions(match_id);
CREATE INDEX idx_predictions_league ON predictions(league_id);
CREATE INDEX idx_predictions_user_league ON predictions(user_id, league_id);

-- Prediction Scores
CREATE TABLE prediction_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID NOT NULL UNIQUE REFERENCES predictions(id) ON DELETE CASCADE,
    exact_score_points INT NOT NULL DEFAULT 0,
    outcome_points INT NOT NULL DEFAULT 0,
    group_position_points INT NOT NULL DEFAULT 0,
    total_points INT NOT NULL DEFAULT 0,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Points validation
    CONSTRAINT chk_exact_points CHECK (exact_score_points IN (0, 3)),
    CONSTRAINT chk_outcome_points CHECK (outcome_points IN (0, 1)),
    CONSTRAINT chk_group_points CHECK (group_position_points BETWEEN 0 AND 3),
    CONSTRAINT chk_total_points CHECK (
        total_points = exact_score_points + outcome_points + group_position_points
    )
);

CREATE INDEX idx_pred_scores_prediction ON prediction_scores(prediction_id);

-- Special Predictions
CREATE TABLE special_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    league_id UUID NOT NULL REFERENCES leagues(id),
    category special_category NOT NULL,
    team_id UUID REFERENCES teams(id),
    player_id UUID REFERENCES players(id),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (user_id, league_id, category),

    CONSTRAINT chk_special_target CHECK (
        team_id IS NOT NULL OR player_id IS NOT NULL
    ),
    CONSTRAINT chk_special_type CHECK (
        (category = 'champion' AND team_id IS NOT NULL AND player_id IS NULL)
        OR (category != 'champion' AND player_id IS NOT NULL AND team_id IS NULL)
    )
);

CREATE INDEX idx_special_pred_user ON special_predictions(user_id);
CREATE INDEX idx_special_pred_league ON special_predictions(league_id);
CREATE INDEX idx_special_pred_user_league ON special_predictions(user_id, league_id);

-- Special Results 
CREATE TABLE special_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category special_category NOT NULL UNIQUE,
    team_id UUID REFERENCES teams(id),
    player_id UUID REFERENCES players(id),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_result_target CHECK (
        team_id IS NOT NULL OR player_id IS NOT NULL
    ),
    CONSTRAINT chk_result_type CHECK (
        (category = 'champion' AND team_id IS NOT NULL AND player_id IS NULL)
        OR (category != 'champion' AND player_id IS NOT NULL AND team_id IS NULL)
    )
);

-- Audit Log
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    entity VARCHAR(100) NOT NULL,
    entity_id UUID,
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_entity ON audit_log(entity, entity_id);
CREATE INDEX idx_audit_created ON audit_log(created_at);