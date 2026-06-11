# Glossary

This glossary defines the main terms used across the World Cup Predictions project.

Its purpose is to keep terminology consistent across the codebase, documentation, API, and future data models.

---

## Product Terms

| Term | Description |
|------|-------------|
| League | A private competition containing participants, predictions and rankings. |
| League Member | A user who participates in a league. |
| League Admin | A league member with permissions to manage league participants and settings. |
| Ranking | Classification of league participants based on points earned. |
| Participant | A user taking part in a prediction league. |

---

## Tournament Terms

| Term | Description |
|------|-------------|
| Team | A national team participating in the tournament. |
| Player | A football player associated with a team. |
| Match | A football match between two teams. |
| Group Stage | Initial tournament phase where teams play within groups. |
| Knockout Stage | Elimination phase where the losing team is eliminated. |
| Bracket | The predefined knockout tournament structure. |
| Placeholder | A temporary reference within the tournament bracket, such as `1A`, `2B`, or `W49`. |

---

## Prediction Terms

| Term | Description |
|------|-------------|
| Prediction | A participant's predicted score for a match. |
| Special Prediction | A tournament-wide prediction, such as Champion, MVP, Golden Boot or Best Goalkeeper. |
| 1X2 | Match outcome: Home Win (1), Draw (X), Away Win (2). |
| Submission Deadline | Latest moment a prediction can be created or modified. |
| Exact Score | A prediction where the participant correctly guesses the final score of a match. |
| Outcome | The final result type of a match: home win, draw, or away win. |
| Group Prediction | A participant's predicted final order (1st to 4th) for a group. |
| Group Standings | The actual final classification of teams within a group, computed from match results. |
| Group Position Points | Points awarded for correctly predicting the final position of a team in a group. 1 point per correct position. |
| Invite Code | A unique code used to join a league. Each league generates one automatically on creation. |

---

## Data & Engineering Terms

| Term | Description |
|------|-------------|
| ETL | Extract, Transform and Load process used to ingest tournament data. |
| Operational Data | Data required for the platform to run, such as teams, matches, predictions and results. |
| Analytics Data | Data prepared for statistics, reporting, dashboards and insights. |
| Data Ingestion | Process of importing data from external sources into the platform. |
| Data Validation | Process of checking whether imported or submitted data respects expected rules. |
| External Link | A mapping between an internal entity (e.g. match UUID) and an external provider's ID. Stored in `match_external_links`. |
| Provider | An external data source identified by name (e.g. `football-data.org`). Multiple providers can coexist. |
| Sync Pipeline | Process that fetches updated match results from an external API and applies changes to the database. |
| Result Sync | The act of checking pending matches, fetching results from the API, and updating status + scores. |