# Data Model

## Overview

The World Cup Predictions platform uses a relational data model designed to support private leagues, tournament management, match predictions, score calculation, rankings, audit logging, and future analytics.

The model evolved from an initial conceptual domain model into a PostgreSQL schema used by the application.

The current model is focused on the operational platform, but it is designed to support future data engineering and analytics workloads.

---

## Modelling Artefacts

The repository contains two modelling artefacts:

- [Initial Domain Model](history/initial-domain-model.png) - first conceptual sketch of the main entities and relationships.
- [ER Diagram](diagrams/er-diagram.pdf) - relational data model used as the basis for the PostgreSQL schema.

---

## Core Domains

The data model is organised around six main domains:

1. Users
2. Leagues
3. Tournament
4. Predictions
5. Special Predictions
6. Group Predictions
7. External Links
8. Audit

---

## 1. Users

The `users` domain is responsible for platform access and authentication.

### Main entity

- `users`

### Purpose

The `users` table stores application users and their authentication-related information.

It supports:

- user registration
- login
- password hashing
- account activation
- platform-level administration through `is_superadmin`

### Key relationships

- A user can create multiple leagues.
- A user can join multiple leagues through `league_members`.
- A user can submit match predictions.
- A user can submit special predictions.
- A user can trigger audit log events.

---

## 2. Leagues

The `leagues` domain is responsible for private prediction competitions.

### Main entities

- `leagues`
- `league_members`

### Purpose

A league represents a private competition where users compete against each other during the tournament.

The `league_members` table connects users and leagues, allowing the same user to participate in multiple leagues with different roles.

### Key rules

- A user can participate in multiple leagues.
- A league can contain multiple users.
- A user has a role inside each league.
- The creator of a league is automatically added as league admin.
- Each league has a unique invite code generated automatically on creation.
- Users join leagues by entering the league's invite code.

### Key relationships

- `leagues.created_by` references `users.id`.
- `league_members.user_id` references `users.id`.
- `league_members.league_id` references `leagues.id`.

---

## 3. Tournament

The `tournament` domain is responsible for representing the World Cup structure.

### Main entities

- `teams`
- `players`
- `matches`

### Purpose

This domain stores the global tournament data shared by all leagues.

Teams, players, matches, match schedules, results, and knockout progression are not league-specific. They exist once and are reused across all private leagues.

### Key rules

- Teams are global.
- Players belong to teams.
- Matches can belong to the group stage or knockout stage.
- A match can reference real teams or placeholders.
- Knockout matches can use placeholders such as `1A`, `2B`, or `W49`.
- Match results are stored globally.
- Submission deadlines are stored per match.

### Key relationships

- `players.team_id` references `teams.id`.
- `matches.home_team_id` references `teams.id`.
- `matches.away_team_id` references `teams.id`.
- `matches.advancing_team_id` references `teams.id`.

---

## 4. Predictions

The `predictions` domain is responsible for match predictions and score calculation.

### Main entities

- `predictions`
- `prediction_scores`

### Purpose

A prediction represents the score submitted by a user for a specific match inside a specific league.

Prediction scores are stored separately from predictions to separate raw user input from calculated data.

### Key rules

- A user can only submit one prediction per match per league.
- Predictions belong to a league.
- Predictions belong to a match.
- Predictions are submitted by users.
- Prediction scores are calculated after match results are available.
- Calculated scores can be recalculated without changing the original prediction.

### Key relationships

- `predictions.user_id` references `users.id`.
- `predictions.match_id` references `matches.id`.
- `predictions.league_id` references `leagues.id`.
- `prediction_scores.prediction_id` references `predictions.id`.

---

## 5. Special Predictions

The `special_predictions` domain is responsible for tournament-wide predictions.

### Main entities

- `special_predictions`
- `special_results`

### Purpose

Special predictions cover tournament outcomes that are not linked to a single match.

Examples include:

- Champion
- MVP
- Golden Boot
- Best Young Player
- Best Goalkeeper

Special results store the real official results used to calculate points.

### Key rules

- Each user can submit one special prediction per category per league.
- Champion predictions reference a team.
- Individual award predictions reference a player.
- Special results are global.
- Special prediction scores can be calculated once official results are recorded.

### Key relationships

- `special_predictions.user_id` references `users.id`.
- `special_predictions.league_id` references `leagues.id`.
- `special_predictions.team_id` references `teams.id`.
- `special_predictions.player_id` references `players.id`.
- `special_results.team_id` references `teams.id`.
- `special_results.player_id` references `players.id`.

---

## 6. Group Predictions

The `group_predictions` domain is responsible for predictions about the final standings of each group.

### Main entity

- `group_predictions`

### Purpose

A group prediction represents a user's predicted final order (1st through 4th) for a specific group within a league.

Unlike match predictions which target individual games, group predictions target the overall outcome of the group stage. They are scored after all group matches are finished by comparing the predicted order with the actual final standings.

### Key rules

- Each user can submit one group prediction per group per league.
- A group prediction references exactly four teams, all from the same group.
- All four teams must be distinct.
- The deadline for submission is before the first match of that group starts.
- Scoring awards 1 point per correctly predicted position (maximum 4 per group, 48 total across 12 groups).
- Points are stored in `points_awarded` (NULL until scored).

### Key relationships

- `group_predictions.user_id` references `users.id`.
- `group_predictions.league_id` references `leagues.id`.
- `group_predictions.first_team_id` references `teams.id`.
- `group_predictions.second_team_id` references `teams.id`.
- `group_predictions.third_team_id` references `teams.id`.
- `group_predictions.fourth_team_id` references `teams.id`.

---

## 7. External Links

The `external_links` domain is responsible for mapping internal entities to external data providers.

### Main entity

- `match_external_links`

### Purpose

The `match_external_links` table connects internal match UUIDs to external provider IDs (e.g. football-data.org API match IDs). This decouples the internal data model from any specific external source and supports multiple providers simultaneously.

The table is used by the ETL pipeline during initial data import and by the sync pipeline when fetching match results.

### Key rules

- Each match can have one link per provider.
- The same external ID cannot be linked to multiple matches within the same provider.
- The `provider` field is a free-text identifier (e.g. `football-data.org`, `api-football`).
- The `external_id` field is stored as text to support different ID formats across providers.
- Links are populated automatically during the ETL load step.

### Key relationships

- `match_external_links.match_id` references `matches.id` (CASCADE on delete).
- Primary key: `(match_id, provider)`.
- Unique constraint: `(provider, external_id)`.

---

## 8. Audit

The `audit` domain is responsible for tracking important system actions.

### Main entity

- `audit_log`

### Purpose

The audit log records relevant operations performed by users or by the system.

It can be used for debugging, traceability, and future analytics.

### Examples of auditable actions

- user registration
- league creation
- member added to league
- prediction submitted
- prediction updated
- match result updated
- score recalculated
- data import completed

### Key relationships

- `audit_log.user_id` references `users.id`.

---

## Design Decisions

### Global tournament data

Tournament data is global to the platform.

This means that teams, players, matches, and real results are stored once and shared across all leagues.

Private leagues only contain league-specific data such as members, predictions, scores, and rankings.

---

### League-specific predictions

Predictions are league-specific.

The same user can participate in multiple leagues and submit different predictions for the same match in each league.

This is supported by the uniqueness rule:

```text
user_id + match_id + league_id
```

This enables the same user to compete independently across leagues with different predictions.

---

### Separation of raw predictions and calculated scores

Prediction scores are stored in a separate table (`prediction_scores`) to ensure the original user input is never modified by the scoring engine.

This design allows scores to be recalculated at any time without losing or altering the submitted predictions.

---

### Group predictions as explicit predictions

Group position points are calculated from explicit group predictions rather than being derived from match predictions.

Users explicitly predict the final order of each group (1st through 4th) before the group starts. This was introduced because colleagues proposed it and the tournament timeline allowed for the feature.

The scoring is separate from match prediction scoring: 1 point per correct position, stored directly on the `group_predictions` table.