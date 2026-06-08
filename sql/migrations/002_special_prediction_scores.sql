-- ============================================
-- Special Prediction Scores
-- Migration: 002_special_prediction_scores.sql
-- ============================================

CREATE TABLE special_prediction_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    special_prediction_id UUID NOT NULL UNIQUE REFERENCES special_predictions(id) ON DELETE CASCADE,
    points_awarded INT NOT NULL DEFAULT 0,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_special_points CHECK (points_awarded IN (0, 6))
);

CREATE INDEX idx_special_prediction_scores_prediction
ON special_prediction_scores(special_prediction_id);
