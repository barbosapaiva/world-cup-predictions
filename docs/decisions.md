# Architecture Decision Records

## ADR-001: PostgreSQL as primary database

**Context:** We needed a database for storing users, leagues, matches, predictions, and rankings. The main candidates were PostgreSQL (relational) and MongoDB (document).

**Decision:** PostgreSQL.

**Rationale:** The data model is heavily relational. Users belong to leagues, predictions reference matches and users, rankings aggregate across predictions. PostgreSQL's foreign keys, joins, and constraints enforce data integrity at the DB level. Custom ENUM types (`match_stage`, `match_status`, `player_position`) map cleanly to domain concepts. MongoDB would require manual join logic and denormalization that adds complexity without benefit for this use case.

---

## ADR-002: SQLAlchemy 2.0 with async (asyncpg)


**Context:** FastAPI is async-native. We needed an ORM/query layer that works well with `async/await` and PostgreSQL.

**Decision:** SQLAlchemy 2.0 with `asyncpg` driver via `create_async_engine`.

**Rationale:** SQLAlchemy 2.0 has first-class async support. Using `asyncpg` gives us high-performance async PostgreSQL access without blocking the event loop. Alembic handles migrations. The alternative (raw asyncpg queries) would sacrifice the ORM's model validation and migration tooling.

One gotcha worth documenting: asyncpg uses `$1, $2` positional params, so the `::type` cast syntax conflicts with SQLAlchemy's `:param` bind syntax. We use `CAST(:param AS type)` instead throughout the codebase.

---

## ADR-003: JWT authentication (stateless)


**Context:** The API needs user authentication. Options considered were session-based (server-side state), JWT (stateless tokens), and OAuth (third-party providers).

**Decision:** JWT Bearer tokens with `PyJWT` and `bcrypt` for password hashing.

**Rationale:** Stateless auth fits our single-server architecture since no session store is needed. Tokens are stored in `localStorage` on the frontend and sent as `Authorization: Bearer <token>`. Token expiry is configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`. For an MVP with a small user base, this is simpler than setting up OAuth providers. We can add OAuth later if needed.

---

## ADR-004: Global tournament data, independent leagues


**Context:** The platform needs to support multiple friend groups playing against each other. We had to decide how matches, teams, and predictions relate to leagues.

**Decision:** Tournament data (teams, matches, players) is global. Leagues are independent scoring groups where users make one prediction per match, and that prediction counts in all their leagues.

**Rationale:** The World Cup is the same for everyone, so duplicating matches per league would be redundant. One prediction per match simplifies the UX since there's no need to submit separately for each league. Rankings are computed per league by aggregating the same predictions with different member lists. This keeps the data model clean and the user experience simple.

---

## ADR-005: Store submission deadlines in the database


**Context:** Predictions must be locked before match kickoff. We needed to decide where to enforce deadlines.

**Decision:** Each match row has a `submission_deadline` column (timestamptz), set to the match `datetime` by default. The API checks this before accepting predictions.

**Rationale:** Storing deadlines in the DB rather than computing them from match time minus N minutes gives us flexibility to adjust deadlines per match if needed, for example in case of delayed kickoffs. The check happens server-side in the prediction endpoint, so the frontend deadline display is cosmetic. The real enforcement is in the API.

---

## ADR-006: Deploy on DigitalOcean Droplet with Docker Compose

**Context:** We needed a hosting solution for the MVP. Candidates considered were DigitalOcean Droplet, Vercel with a managed DB, Railway, Fly.io, and AWS EC2.

**Decision:** Single DigitalOcean Droplet ($4-6/month) running Docker Compose with Nginx, FastAPI, React, and PostgreSQL.

**Rationale:** At $4-6/month for a Basic Droplet (1 vCPU, 1 GB RAM, 25 GB SSD), this is the cheapest option that gives full control. Railway and Fly.io charge per-service and can exceed $15-20/month for the same stack. AWS EC2 has similar pricing but more operational complexity.

Docker Compose mirrors the dev setup, so it's the same `docker compose up` workflow locally and in production with no new tools to learn. We own the server, meaning we can SSH in, inspect logs, run database queries, and debug issues directly. Managed platforms abstract this away, which is great for teams but limits learning.

Running your own server, configuring Nginx, setting up SSL with Certbot, and writing backup scripts also demonstrates ops skills that managed platforms hide, which adds portfolio value.

A single Droplet handles the expected load for a small group of friends. If the platform grows, we can scale vertically ($12/month for 2 GB RAM) or migrate to a managed solution.

**Trade-offs accepted:** We handle our own backups, SSL renewal, and security updates. There's no auto-scaling and it's a single point of failure. These are acceptable for an MVP with a small user base.
---

## ADR-007: Global invite code for registration

**Context:** The platform is for a small group of friends. We needed a way to prevent random people from registering while keeping the sign-up process simple.

**Decision:** A single invite code stored as an environment variable (`INVITE_CODE`). The registration endpoint requires this code. Everyone who should have access gets the same code shared privately.

**Rationale:** For a friends-only platform, a full invite system with per-user codes, expiration dates, and usage limits is overkill. A single shared code is enough to keep strangers out. It's zero-migration since no new tables are needed, and the code lives in `.env.prod` alongside the other secrets. If the code leaks, we just change the env var and restart. If we later need per-user invites, we can add an `invite_codes` table without breaking anything.

---

## ADR-008: Per-league invite codes

**Context:** With multiple leagues possible, we needed a way for users to join a specific league without requiring an admin to manually add them. The global invite code (ADR-007) controls registration, but league membership needed its own mechanism.

**Decision:** Each league gets a unique 8-character invite code generated automatically on creation. Users join by entering the code. The code is stored in `leagues.invite_code` (unique, not null).

**Rationale:** This keeps the flow simple: create a league, share the code with friends, they join themselves. No admin approval step needed for a friends-only platform. The code is auto-generated from a UUID to avoid collisions. If a code leaks, the league admin can see who joined and remove unwanted members. A more complex system with expiring or single-use codes wasn't needed for this scale.

---

## ADR-009: Explicit group predictions

**Context:** The scoring system had a `group_position_points` field in `prediction_scores` but no mechanism for users to predict group standings. Colleagues proposed adding this feature while there was still time before the tournament.

**Decision:** Add explicit group predictions as a new prediction type. Users predict the final order (1st through 4th) for each group before the group's first match. Scoring awards 1 point per correct position (max 4 per group, 48 total).

**Rationale:** Two approaches were considered: deriving standings from match predictions (simulating a table from the predicted scores) or having users explicitly predict the order. Explicit prediction was chosen because it's clearer to the user, simpler to implement, and creates a distinct prediction type that's independently valuable.

The deadline is per-group (before the first match of that group) rather than a global deadline, giving users more time to adjust as the tournament unfolds. Scoring is stored directly on the `group_predictions` row (`points_awarded`) rather than in a separate scores table, since the relationship is 1:1 and there's no need for recalculation history.

**Trade-offs accepted:** The `group_position_points` field in `prediction_scores` becomes unused. It remains in the schema for backward compatibility but is always 0. Group prediction points are summed separately in the ranking query via a subquery on `group_predictions.points_awarded`.
