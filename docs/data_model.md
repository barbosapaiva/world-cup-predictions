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
6. Audit

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

## 6. Audit

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