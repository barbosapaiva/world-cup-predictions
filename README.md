# ⚽ World Cup Predictions

> The World Cup is coming. It's time to settle, once and for all, who knows football best.

World Cup Predictions is a platform designed to replace spreadsheets, endless group chats, and manual score calculations with an automated and interactive experience for football fans.

Besides being a fun project to play with friends, this repository is a real-world software engineering project that combines modern Backend Engineering and Data Engineering practices.

---

## 💡 Why this project?

Prediction games have become a tradition during major football tournaments. Friends, families, and colleagues create leagues to compete against each other by predicting match results and tournament outcomes.

Unfortunately, most of these competitions are still managed using spreadsheets and messaging apps, creating unnecessary manual work for the organiser and offering little visibility throughout the tournament.

World Cup Predictions aims to solve that problem by providing a platform where users can:

- Create private leagues
- Invite friends
- Submit match predictions
- Make special tournament predictions
- Follow rankings in real time
- Track statistics throughout the competition

At the same time, the project serves as a practical exercise in designing and building a complete backend application supported by data engineering workflows.

---

## 🌍 Overview

The project evolves in two major phases.

### Phase 1 - Operational Platform

Build the core platform required to run prediction leagues.

Main features:

- User authentication
- Private leagues
- Tournament management
- Teams and players
- Match predictions
- Special predictions
- Automatic scoring
- Rankings
- Tournament data ingestion

### Phase 2 - Analytics Platform

Transform operational data into valuable insights.

Main features:

- Historical statistics
- Prediction accuracy
- User performance metrics
- League analytics
- Tournament insights
- Advanced ETL pipelines
- Automated reporting
- Dashboards

---

## 🎯 Project Goals

This project aims to combine multiple software engineering disciplines.

### Backend Engineering

- REST API design
- Authentication and authorisation
- Business logic implementation
- Repository Pattern
- Service Layer
- Clean code principles

### Data Engineering

- ETL pipelines
- Data ingestion
- Relational data modelling
- Tournament synchronisation
- Automatic score calculations
- Data validation
- Statistics generation

### Software Engineering

- Domain modelling
- System design
- Documentation
- Docker
- API design
- CI/CD
- Testing

---

## 🛠 Tech Stack

### Backend

- FastAPI
- SQLAlchemy Async
- PostgreSQL
- JWT Authentication
- bcrypt

### Data

- Python
- ETL Pipelines
- Relational Data Modelling

### DevOps

- Docker
- Docker Compose
- uv
- Ruff

### Documentation

- OpenAPI
- Swagger UI
- ReDoc

---

## 🚀 Features

### Authentication & Security

- User registration
- User login
- JWT authentication
- Password hashing
- Protected endpoints
- Role-based permissions

### League Management

- Create private leagues
- League administrators
- Invite members
- Manage participants

### Tournament

- Teams
- Players
- Matches
- Group stage
- Knockout stage
- Automatic bracket progression

### Predictions

- Match predictions
- Special tournament predictions
- Prediction deadlines
- Prediction updates

### Rankings

- Automatic scoring
- League standings
- User statistics
- Performance tracking

### Data Pipelines

- Tournament data ingestion
- Team synchronisation
- Player synchronisation
- Match updates
- Result updates
- ETL workflows

---

## 📈 Project Evolution

The project follows an iterative approach.

The initial goal is to build a fully functional prediction platform for the FIFA World Cup.

As the platform evolves, additional engineering artefacts such as architecture diagrams, analytics pipelines, advanced documentation, and reporting capabilities will be introduced.

This approach ensures that the project remains functional while continuously improving from both a software engineering and data engineering perspective.

---

## 🚧 Project Status

The project is currently under active development.

Current focus:

- Tournament management
- Prediction engine
- Automatic scoring
- Rankings
- Operational ETL

Future improvements:

- Advanced analytics
- Historical statistics
- Dashboards
- Enhanced data pipelines
- Performance metrics

---

## 🛣 Roadmap

The project roadmap is maintained in the documentation folder.

See:

- [Roadmap](docs/roadmap.md)

---

## 📚 Documentation

Project documentation is organised in the `docs/` folder.

Available documentation:

- [Data Model](docs/data_model.md)
- [Glossary](docs/glossary.md)
- [Roadmap](docs/roadmap.md)

Available diagrams:

- [Initial Domain Model](docs/history/initial-domain-model.png)
- [ER Diagram](docs/diagrams/er-diagram.pdf)

Planned documentation:

- Architecture
- Actors
- Business rules
- Use cases
- API documentation
- Deployment
- Decision log
- Additional diagrams

---

## 🧩 Diagrams

The repository already includes the first modelling artefacts used during the project design.

Available diagrams:

- [Initial Domain Model](docs/history/initial-domain-model.png) - first conceptual sketch of the main entities and relationships.
- [ER Diagram](docs/diagrams/er-diagram.pdf) - relational data model used as the basis for the PostgreSQL schema.

Additional architecture and flow diagrams will be added as the project evolves.

## 🤝 Contributing

Suggestions, ideas, and improvements are always welcome.

---

## 📄 License

This project is developed for educational, portfolio, and personal use.