# Finance Planner Backend

FastAPI-based REST API for the Finance Planner web application. Handles user authentication, scenario management, simulation execution, and What-If exploration with persistence.

## Quick Start

### Setup

```bash
cd web/backend
pip install -r requirements.txt
```

### Running the Server

**Development (with auto-reload):**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Production:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Server will be available at `http://localhost:8000`

API documentation (Swagger UI): `http://localhost:8000/docs`

### Health Check

```bash
curl http://localhost:8000/health
# Response: {"status": "ok"}
```

---

## Architecture Overview

```
web/backend/
├── main.py                  # FastAPI app initialization & router registration
├── requirements.txt         # Python dependencies
├── database.py             # SQLAlchemy setup, session management
├── auth.py                 # JWT authentication, get_current_user dependency
├── models.py               # SQLAlchemy ORM models (Profile, SimulationRun, ScenarioResult, YearData)
├── schemas.py              # Pydantic request/response validation models
└── routers/
    ├── auth.py             # User login, token generation
    ├── profiles.py         # Profile CRUD operations
    ├── scenarios.py        # Scenario retrieval and detail endpoints
    ├── simulate.py         # One-off What-If simulation (stateless)
    └── whatif_saves.py     # Persist What-If explorations as named scenarios
```

### Design Principles

1. **Layered Architecture** — Routers (HTTP) → Domain (business logic) → Infrastructure (data loading)
2. **Dependency Injection** — FastAPI's `Depends()` pattern for DB, auth, etc.
3. **Type Safety** — Pydantic for validation, SQLAlchemy for ORM
4. **Domain-Driven** — Heavy lifting happens in `/domain/` (simulation, insights)
5. **Concurrent Safety** — File locking for scenarios.json writes
6. **Stateless** — Each request is independent; session data in DB

---

## Configuration

### Database

SQLite database stored at `data/finance_planner.db` (relative to project root).

**Full path:** `/Users/alon/Documents/finance_planner/data/finance_planner.db`

Initialized automatically on first run via `init_db()` in `main.py`.

**Models:**
- `Profile` — User profiles (id, name, display_name, description, created_at)
- `SimulationRun` — Batch runs (id, profile_id, label, generated_at, num_scenarios)
- `ScenarioResult` — Individual scenario within a run (id, run_id, scenario_name, retirement_year)
- `YearData` — Year-by-year data for a scenario (year, age, income, expenses, portfolio, etc.)

### CORS

Configured for local development:
```python
allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"]
```

Update `main.py` for production domains.

### Authentication

Uses JWT tokens (issued during login). Token required for:
- Profile endpoints
- Scenario retrieval
- Saving What-If scenarios

Header format: `Authorization: Bearer <token>`

---

## Key Concepts

### Profiles

A profile represents a user's financial context. Each profile has:
- **scenarios.json** — Named scenario definitions (income, expenses, events, etc.)
- **settings.json** — Simulation defaults (years, return rate, etc.)
- **scenario_nodes.json** — Inheritance tree for scenario variations
- **SQLite records** — Simulation runs and results

Profiles are loaded from the domain via `infrastructure.data_layer.get_scenarios_path()`.

### Scenarios

Two types of scenarios:

1. **Stored Scenarios** — Defined in `scenarios.json`, parsed and loaded on demand
2. **Saved What-If Scenarios** — User-created via the "Save as Scenario" feature
   - Appended to `scenarios.json` with `"saved_from": "whatif"` marker
   - Tracked in SQLite under the "What-If Saves" `SimulationRun`
   - Immediately available in the scenario list

### Simulation Flow

1. **Frontend** — User adjusts sliders (income, expenses, growth rate, age, portfolio, events)
2. **POST /api/v1/simulate** — Stateless "What-If" simulation (no persistence)
   - Returns year-by-year data for the scenario
   - Used in real-time exploration
3. **POST /api/v1/profiles/{profile_id}/saved-scenarios** — User clicks "Save as Scenario"
   - Backend runs simulation in-process
   - Appends to disk with file lock (atomic)
   - Records result in SQLite
   - Scenario now appears in Scenarios list under "What-If Saves" run

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | Latest | Web framework |
| `uvicorn` | Latest | ASGI server |
| `sqlalchemy` | Latest | ORM |
| `pydantic` | Latest | Request/response validation |
| `filelock` | ≥3.12.0 | Concurrent JSON write safety |
| `python-multipart` | Latest | Form data parsing |

See `requirements.txt` for pinned versions.

---

## Request/Response Patterns

### Successful Response

```json
{
  "data": { /* response payload */ },
  "timestamp": "2026-04-13T10:30:00Z"
}
```

### Error Response

```json
{
  "detail": "Profile not found"
}
```

HTTP status codes follow REST conventions:
- `200 OK` — Successful GET
- `201 Created` — Resource created (e.g., POST /saved-scenarios)
- `400 Bad Request` — Invalid input
- `401 Unauthorized` — Missing/invalid token
- `404 Not Found` — Resource not found
- `409 Conflict` — Duplicate scenario name
- `500 Internal Server Error` — Server error

---

## Routers

### Authentication (`auth.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/login` | POST | Issue JWT token |

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

---

### Profiles (`profiles.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/profiles` | GET | List all profiles |
| `/api/v1/profiles/{profile_id}` | GET | Get profile details |

**Response:**
```json
{
  "id": 1,
  "name": "alon",
  "display_name": "Alon's Profile",
  "description": "Alon's financial plan",
  "created_at": "2026-04-13T10:00:00Z"
}
```

---

### Scenarios (`scenarios.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/profiles/{profile_id}/runs` | GET | List simulation runs |
| `/api/v1/runs/{run_id}/scenarios` | GET | List scenarios in run |
| `/api/v1/scenarios/{scenario_id}` | GET | Get scenario details |
| `/api/v1/scenarios/{scenario_id}/summary` | GET | Get scenario summary |

---

### Simulation (`simulate.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/simulate` | POST | Run one-off What-If simulation |

**Request:**
```json
{
  "monthly_income": 50000,
  "monthly_expenses": 25000,
  "return_rate": 0.07,
  "starting_age": 41,
  "initial_portfolio": 2000000,
  "years": 20,
  "events": [
    {
      "year": 5,
      "portfolio_injection": 500000,
      "description": "Bonus payout"
    }
  ]
}
```

**Response (200):**
```json
{
  "scenario_name": "What-If Simulation",
  "retirement_year": 11,
  "final_portfolio": 18500000,
  "total_savings": 16500000,
  "year_data": [
    {
      "year": 1,
      "age": 41,
      "income": 50000,
      "expenses": 25000,
      "net_savings": 25000,
      "portfolio": 2025000,
      "required_capital": 500000,
      "mortgage_active": false,
      "pension_value": 0,
      "pension_accessible": false
    },
    ...
  ]
}
```

---

### What-If Saves (`whatif_saves.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/profiles/{profile_id}/saved-scenarios` | POST | Save What-If as named scenario |

**Request:**
```json
{
  "scenario_name": "Conservative Plan",
  "monthly_income": 50000,
  "monthly_expenses": 20000,
  "return_rate": 0.06,
  "starting_age": 41,
  "initial_portfolio": 2000000,
  "years": 20,
  "events": []
}
```

**Response (201):**
```json
{
  "scenario_result_id": 42,
  "run_id": 2,
  "scenario_name": "Conservative Plan",
  "retirement_year": 12,
  "final_portfolio": 17500000
}
```

**Error (409):**
```json
{
  "detail": "A scenario named 'Conservative Plan' already exists."
}
```

---

## File Organization

### Routers

Each router is a FastAPI `APIRouter` with a prefix and set of endpoints:

```python
router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])

@router.get("")
def list_profiles(...):
    ...
```

Routers are registered in `main.py`:
```python
app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(scenarios.router)
app.include_router(simulate.router)
app.include_router(whatif_saves.router)
```

### Models vs Schemas

- **Models** (`models.py`) — SQLAlchemy ORM models (map to database tables)
- **Schemas** (`schemas.py`) — Pydantic models (validate HTTP requests/responses)

Example:
```python
# models.py (database)
class ScenarioResult(Base):
    __tablename__ = "scenario_results"
    id = Column(Integer, primary_key=True)
    scenario_name = Column(String)

# schemas.py (HTTP)
class ScenarioResultSchema(BaseModel):
    id: int
    scenario_name: str
    retirement_year: Optional[int]
    year_data: List[YearDataSchema]
```

---

## Testing

Run the backend directly to test:

```bash
# Quick test of imports and startup
python3 -c "import main; print('✓ Backend imports successfully')"

# Start server with auto-reload
uvicorn main:app --reload

# In another terminal, test an endpoint
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/profiles -H "Authorization: Bearer <token>"
```

---

## Common Tasks

### Add a New Endpoint

1. **Create router file** (e.g., `routers/reports.py`):
   ```python
   from fastapi import APIRouter
   router = APIRouter(prefix="/api/v1/reports", tags=["reports"])
   
   @router.get("")
   def list_reports(...):
       ...
   ```

2. **Register in `main.py`**:
   ```python
   from routers import reports
   app.include_router(reports.router)
   ```

3. **Add schemas** to `schemas.py` if needed.

### Modify Database Schema

1. **Update `models.py`** with new fields
2. **Call `init_db()`** to recreate tables (development only; production requires migration)

### Add Authentication to Endpoint

```python
@router.get("/{item_id}")
def get_item(item_id: int, username: str = Depends(get_current_user), db: Session = Depends(get_db)):
    # username is guaranteed to be authenticated
    # db is a fresh SQLAlchemy session
    ...
```

---

## Debugging

### Check Backend Logs

```bash
# Server logs show incoming requests and errors
uvicorn main:app --reload
```

### Test Authentication

```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' \
  | jq -r '.access_token')

# Use token in request
curl http://localhost:8000/api/v1/profiles \
  -H "Authorization: Bearer $TOKEN"
```

### Debug Simulations

The domain's `simulate()` function is deterministic. If a simulation result differs:
1. Check input parameters (income, expenses, return rate, age)
2. Verify events are correct (year, amount)
3. Compare with command-line simulation: `python main.py` in project root

---

## Deployment

For production deployment:

1. **Update CORS origins** in `main.py` for your domain
2. **Set up proper database** (PostgreSQL recommended instead of SQLite)
3. **Use environment variables** for secrets (JWT_SECRET, DB_URL, etc.)
4. **Run with gunicorn** or similar:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 main:app
   ```
5. **Set up SSL/TLS** via reverse proxy (nginx, Cloudflare, etc.)

---

## Related Documentation

- [API Reference](API.md) — Detailed endpoint reference
- [Backend Architecture](ARCHITECTURE.md) — Design patterns and data flow
- [Main Project CLAUDE.md](../../CLAUDE.md) — Overall project setup and principles
- [Domain Layer](../../domain/DOMAIN.md) — Simulation engine and business logic
