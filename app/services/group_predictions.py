from uuid import UUID

from fastapi import HTTPException, status

from app.models.enums import MatchStage, MatchStatus
from app.models.group_predictions import GroupPrediction
from app.models.users import User
from app.repositories.group_predictions import GroupPredictionRepository
from app.repositories.leagues import LeagueRepository
from app.repositories.tournament import TournamentRepository
from app.schemas.group_predictions import GroupPredictionCreate, GroupStandingEntry


class GroupPredictionService:
    def __init__(
        self,
        repo: GroupPredictionRepository,
        league_repo: LeagueRepository,
        tournament_repo: TournamentRepository,
    ):
        self.repo = repo
        self.league_repo = league_repo
        self.tournament_repo = tournament_repo

    async def submit_prediction(
        self,
        league_id: UUID,
        data: GroupPredictionCreate,
        current_user: User,
    ) -> GroupPrediction:
        # Verify league membership
        member = await self.league_repo.get_member(current_user.id, league_id)
        if member is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member of this league")

        # Verify group exists and teams belong to it
        group_teams = await self.tournament_repo.list_teams_by_group(data.group_letter)
        if len(group_teams) == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Group {data.group_letter} not found")

        group_team_ids = {t.id for t in group_teams}
        submitted_ids = {data.first_team_id, data.second_team_id, data.third_team_id, data.fourth_team_id}

        if not submitted_ids.issubset(group_team_ids):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "All teams must belong to the specified group")

        # Check deadline: before the first match of this group
        group_matches = await self.tournament_repo.list_matches(stage=MatchStage.GROUP)
        group_matches = [m for m in group_matches if m.group_letter == data.group_letter]

        if group_matches:
            first_match = min(group_matches, key=lambda m: m.match_date)
            if first_match.status != MatchStatus.SCHEDULED:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Deadline passed — group {data.group_letter} already started",
                )

        prediction = GroupPrediction(
            user_id=current_user.id,
            league_id=league_id,
            group_letter=data.group_letter.upper(),
            first_team_id=data.first_team_id,
            second_team_id=data.second_team_id,
            third_team_id=data.third_team_id,
            fourth_team_id=data.fourth_team_id,
        )

        return await self.repo.upsert(prediction)

    async def list_my_predictions(
        self,
        league_id: UUID,
        current_user: User,
    ) -> list[GroupPrediction]:
        member = await self.league_repo.get_member(current_user.id, league_id)
        if member is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member of this league")

        return await self.repo.list_by_user_league(current_user.id, league_id)

    async def get_group_standings(self, group_letter: str) -> list[GroupStandingEntry]:
        """Compute actual group standings from finished match results."""
        all_group_matches = await self.tournament_repo.list_matches(stage=MatchStage.GROUP)
        matches = [m for m in all_group_matches if m.group_letter == group_letter and m.status == MatchStatus.FINISHED]

        teams = await self.tournament_repo.list_teams_by_group(group_letter)
        if not teams:
            return []

        stats: dict[UUID, dict] = {}
        for t in teams:
            stats[t.id] = {
                "team_id": t.id,
                "team_name": t.name,
                "team_code": t.code,
                "played": 0,
                "won": 0,
                "drawn": 0,
                "lost": 0,
                "goals_for": 0,
                "goals_against": 0,
            }

        for m in matches:
            if m.home_team_id is None or m.away_team_id is None:
                continue
            if m.home_score is None or m.away_score is None:
                continue

            h, a = stats.get(m.home_team_id), stats.get(m.away_team_id)
            if h is None or a is None:
                continue

            h["played"] += 1
            a["played"] += 1
            h["goals_for"] += m.home_score
            h["goals_against"] += m.away_score
            a["goals_for"] += m.away_score
            a["goals_against"] += m.home_score

            if m.home_score > m.away_score:
                h["won"] += 1
                a["lost"] += 1
            elif m.home_score < m.away_score:
                a["won"] += 1
                h["lost"] += 1
            else:
                h["drawn"] += 1
                a["drawn"] += 1

        entries = []
        for s in stats.values():
            s["goal_difference"] = s["goals_for"] - s["goals_against"]
            s["points"] = s["won"] * 3 + s["drawn"]
            entries.append(s)

        # Sort: points desc, goal diff desc, goals for desc
        entries.sort(key=lambda x: (-x["points"], -x["goal_difference"], -x["goals_for"]))

        return [GroupStandingEntry(position=i + 1, **e) for i, e in enumerate(entries)]

    async def score_group(self, league_id: UUID, group_letter: str) -> None:
        """Score all predictions for a group after it finishes."""
        standings = await self.get_group_standings(group_letter)
        if not standings or standings[0].played == 0:
            return

        actual_order = [s.team_id for s in standings]
        predictions = await self.repo.list_by_league_group(league_id, group_letter)

        for pred in predictions:
            predicted_order = [
                pred.first_team_id,
                pred.second_team_id,
                pred.third_team_id,
                pred.fourth_team_id,
            ]
            points = sum(1 for predicted, actual in zip(predicted_order, actual_order) if predicted == actual)
            await self.repo.update_points(pred.id, points)
