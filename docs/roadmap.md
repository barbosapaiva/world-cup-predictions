# Roadmap

This roadmap tracks the planned evolution of the World Cup Predictions platform.

The project is being developed in two main phases:

- **Phase 1 - Operational Platform**: build the core application needed to run private prediction leagues.
- **Phase 2 - Analytics Platform**: transform operational data into statistics, insights, and reporting.

---

## Phase 1 - Operational Platform

The goal of this phase is to build a complete platform capable of running private prediction leagues during the FIFA World Cup.

### Authentication & Security

- [x] User registration
- [x] User login
- [x] JWT authentication
- [x] Password hashing
- [x] Current user dependency
- [x] Role management

### Users

- [x] Create users
- [x] List users
- [x] Get user details
- [x] Update users

### Leagues

- [x] Create private leagues
- [x] Add league creator as admin
- [x] List user leagues
- [x] Add league members
- [x] List league members
- [ ] Update league details
- [ ] Manage member roles
- [ ] Remove league members

### Tournament

- [x] Create teams
- [x] List teams
- [x] Filter teams by group
- [x] Create players
- [x] List players by team
- [x] Create matches
- [x] List matches
- [x] Update match results
- [x] Resolve knockout placeholders
- [ ] Improve bracket management
- [ ] Add tournament data import commands

### Predictions

- [x] Submit match predictions
- [x] Update predictions before deadline
- [x] Block predictions after deadline
- [x] Validate league membership before prediction
- [x] Validate knockout advancing team
- [x] List user predictions
- [x] List match predictions

### Special Predictions

- [x] Submit champion prediction
- [x] Submit MVP prediction
- [x] Submit Golden Boot prediction
- [x] Submit Best Young Player prediction
- [x] Submit Best Goalkeeper prediction
- [x] Record official special results
- [x] Calculate special prediction points

### Scoring

- [x] Calculate exact score points
- [x] Calculate 1X2 outcome points
- [ ] Calculate group position points
- [x] Calculate special prediction points
- [x] Recalculate scores after result updates
- [x] Store calculated scores separately from predictions

### Rankings

- [ ] Generate league standings
- [ ] Apply tie-break rules
- [ ] Track user score totals
- [ ] Show ranking by league
- [ ] Show ranking evolution over time

### Operational Data Ingestion

- [ ] Import teams
- [ ] Import players
- [ ] Import matches
- [ ] Import match results
- [ ] Validate imported data
- [ ] Log import executions

---

## Phase 2 - Analytics Platform

The goal of this phase is to transform operational data into insights, metrics, and reports.

### Analytics

- [ ] Historical rankings
- [ ] Prediction accuracy
- [ ] User performance metrics
- [ ] League statistics
- [ ] Tournament insights
- [ ] Most predicted teams
- [ ] Most unpredictable matches

### Data Engineering

- [ ] Advanced ETL workflows
- [ ] Data quality checks
- [ ] Historical datasets
- [ ] Analytics tables
- [ ] Materialized views
- [ ] Incremental data processing

### Reporting

- [ ] Dashboards
- [ ] Automated reports
- [ ] Tournament summary reports
- [ ] League performance reports

---

## Engineering Improvements

These improvements can be implemented gradually throughout both phases.

### Testing

- [ ] Unit tests for services
- [ ] Integration tests for API endpoints
- [ ] Test database setup
- [ ] Scoring engine test cases

### CI/CD

- [ ] GitHub Actions
- [ ] Ruff check
- [ ] Ruff format check
- [ ] Test execution in CI
- [ ] Docker build validation

### Documentation

- [x] README
- [x] Data model documentation
- [x] Glossary
- [x] Roadmap
- [ ] Architecture documentation
- [ ] Business rules
- [ ] Use cases
- [ ] Deployment documentation
- [ ] Decision log

---

## Future Ideas

These ideas are not part of the initial scope but may be explored later.

- Public leagues
- Mobile application
- Prediction notifications
- Machine learning experiments
- Tournament simulations
- AI predictor participant
- Social sharing
- Admin dashboard