# Finance Planner Web App — MVP

A web application for viewing and analyzing financial simulations. Built with FastAPI + Vue 3 + SQLite.

## Setup

### Backend

```bash
cd web/backend

# Install dependencies (first time)
pip install -r requirements.txt

# Seed database (first time)
python seed.py

# Start server
python main.py
```

Backend runs on: **http://localhost:8000**
API docs: **http://localhost:8000/docs** (Swagger UI)

### Frontend

```bash
cd web/frontend

# Install dependencies (first time)
npm install

# Start dev server
npm run dev
```

Frontend runs on: **http://localhost:5173**

## Usage

1. Open **http://localhost:5173** in your browser
2. Login with:
   - Username: `alon`
   - Password: `alon123`
3. Browse profiles and simulation runs
4. View scenarios with portfolio growth charts and year-by-year tables

## Architecture

### Backend (FastAPI)
- `main.py` — App entry point
- `database.py` — SQLite setup
- `models.py` — SQLAlchemy ORM models
- `schemas.py` — Pydantic response schemas
- `auth.py` — JWT authentication
- `seed.py` — Database seeding from Alon profile cache
- `routers/` — API endpoints (auth, profiles, scenarios)

### Frontend (Vue 3)
- `src/views/` — Pages (Login, Dashboard, Scenarios, ScenarioDetail)
- `src/components/` — Reusable components (PortfolioChart, YearDataTable)
- `src/stores/` — Pinia state management (auth store)
- `src/router/` — Vue Router configuration

### Database (SQLite)
- `users` — Authentication
- `profiles` — User profiles (maps to data/profiles/{name}/)
- `simulation_runs` — Cached simulation runs
- `scenario_results` — Scenario data per run
- `year_data` — Year-by-year simulation output

## API Endpoints

All endpoints (except login) require Bearer JWT token.

```
POST   /api/v1/auth/login
GET    /api/v1/profiles
GET    /api/v1/profiles/:profileId/runs
GET    /api/v1/runs/:runId/scenarios
GET    /api/v1/scenarios/:resultId
GET    /api/v1/scenarios/:resultId/summary
```

## Features (MVP)

✅ Simple JWT login  
✅ View profiles and simulation runs  
✅ View scenarios with retirement year and final portfolio  
✅ Portfolio growth chart (line chart with multiple series)  
✅ Year-by-year data table with currency formatting  
✅ Desktop-only layout  

## Future Enhancements

- Input forms to create/edit scenarios
- Israeli defaults and profile templates
- AI-based insights generation
- User registration and multi-user support
- Mobile layout optimization
- Scenario comparison views
- Export/sharing functionality

## Troubleshooting

### Backend not responding
```bash
# Check if port 8000 is in use
lsof -i :8000

# Verify database exists
ls -la data/finance_planner.db
```

### Frontend build issues
```bash
# Clear node_modules and reinstall
rm -rf web/frontend/node_modules
npm install
```

### Database needs reset
```bash
# Remove old database and re-seed
rm data/finance_planner.db
python web/backend/seed.py
```

## Development Notes

- Backend uses sync SQLAlchemy (no async for MVP)
- Frontend uses Vue 3 Composition API
- Chart.js for portfolio visualizations
- Simple PBKDF2 hashing for passwords (upgrade in production)
- CORS enabled for localhost development
