# Backend Architecture

Technical design documentation for the Finance Planner backend.

---

## Layered Architecture

The backend follows a 4-layer, responsibility-based architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                        HTTP Layer                            │
│                  (FastAPI routers, auth)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Data Validation Layer                       │
│               (Pydantic schemas, type safety)                │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Application Layer                           │
│         (Routers + Business Logic + Database ORM)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Domain & Infrastructure Layers                  │
│    (Simulation, Insights, Config loading, Data persistence)  │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

**HTTP Layer** (`routers/*.py`)
- Handle HTTP requests and responses
- Route requests to appropriate handlers
- Manage CORS and error formatting
- Dependency injection for auth/db

**Data Validation** (`schemas.py`)
- Pydantic models for request validation
- Type safety and schema documentation
- Automatic OpenAPI schema generation

**Application Layer**
- Router handler functions
- Database queries (SQLAlchemy ORM)
- Business logic coordination
- Error handling and validation

**Domain/Infrastructure**
- Pure simulation logic (`domain/`)
- Configuration loading (`infrastructure/`)
- Data persistence (file I/O, JSON parsing)

### Key Principle: Layered Dependencies

Each layer depends only on layers below. No circular dependencies.

```
HTTP ←─ Schemas ←─ App ←─ Domain/Infrastructure ←─ (Python stdlib)
```

---

## Request/Response Flow

### Example: Save What-If Scenario

```
User clicks "Save as Scenario"
↓
Frontend builds request:
{
  "scenario_name": "Conservative Plan",
  "monthly_income": 50000,
  "monthly_expenses": 20000,
  ...
}
↓
POST /api/v1/profiles/1/saved-scenarios
↓
[FastAPI Router]
  - Dependency injection:
    - get_current_user() → validates JWT token
    - get_db() → provides SQLAlchemy session
  - Extract path param: profile_id = 1
  - Parse + validate request body (SaveScenarioRequest)
↓
[Handler: save_whatif_scenario]
  1. Validate profile exists → query DB
  2. Check scenario name is unique → query scenario_definitions table
  3. Create Scenario object from request params
  4. Call simulate() from domain layer → run simulation
  5. Insert into scenario_definitions table → create scenario record
  6. Insert into scenario_events table → link events via scenario_id FK
  7. Insert into scenario_mortgages table if mortgage exists
  8. Get-or-create "What-If Saves" SimulationRun
  9. Insert ScenarioResult + YearData rows
  10. Commit transaction
↓
Return SaveScenarioResponse (201 Created)
{
  "scenario_result_id": 42,
  "run_id": 2,
  "scenario_name": "Conservative Plan",
  "retirement_year": 12,
  "final_portfolio": 17500000
}
↓
Frontend receives response, shows success message
User navigates to Scenarios → sees new scenario in "What-If Saves"
```

---

## Data Flow: Saving Scenarios

When a user saves a What-If scenario, data is persisted to SQLite as the source of truth:

### Database Persistence (SQLite)

```
SaveToDatabase()
  ↓
  1. Validate profile exists → query profiles table
  ↓
  2. Check name uniqueness
     - Query: scenario_definitions where profile_id=1 and name="Conservative Plan"
     - If exists: return 409 Conflict
  ↓
  3. Insert into scenario_definitions table
     - name, age, initial_portfolio
     - monthly_income, monthly_expenses (as JSON)
     - return_rate, withdrawal_rate, retirement_mode
     - saved_from = "whatif"
     - saved_at = ISO timestamp
     - profile_id = 1
  ↓
  4. Insert into scenario_events table
     - For each event: insert (scenario_id FK, year, portfolio_injection, description)
  ↓
  5. Insert into scenario_mortgages table (if mortgage exists)
     - scenario_id FK, principal, annual_rate, duration_years
  ↓
  6. Get-or-create "What-If Saves" SimulationRun
     - Query: SimulationRun where profile_id=1 and label="What-If Saves"
     - If exists: reuse
     - If not: create new record
  ↓
  7. Insert ScenarioResult
     - run_id = (from step 6)
     - scenario_id = (from step 3) ← Links to definition
     - scenario_name = "Conservative Plan"
     - retirement_year = (from simulation)
  ↓
  8. Insert YearData rows (one per simulated year)
     - result_id FK, year, age, income, expenses, portfolio, ...
  ↓
  9. Update SimulationRun.num_scenarios
     - Count all ScenarioResult rows for this run
  ↓
  10. Commit transaction
  ↓
Result: Scenario fully stored in database, queryable via REST API
```

**Database Schema:**

```
Profile
├── id (PK)
└── scenario_definitions (1:many)
   ├── id (PK)
   ├── name, age, initial_portfolio
   ├── monthly_income, monthly_expenses (JSON TEXT)
   ├── return_rate, withdrawal_rate, retirement_mode
   ├── saved_from, saved_at, is_deleted
   ├── scenario_events (1:many)
   │  ├── year, portfolio_injection, description
   ├── scenario_mortgages (0:1)
   │  ├── principal, annual_rate, duration_years
   └── scenario_pensions (0:1)
      ├── initial_value, monthly_contribution, annual_growth_rate
     
SimulationRun
├── id (PK)
├── profile_id (FK)
├── generated_at (timestamp)
├── num_scenarios (count)
└── label (optional, "What-If Saves" for user saves)
     ↓
     ├── scenario_results (many)
     │  ├── id (PK)
     │  ├── scenario_id (FK → scenario_definitions) ← Links to definition
     │  ├── scenario_name
     │  ├── retirement_year
     │  └── year_data (many)
     │     ├── year, age, income, expenses, portfolio, ...
```

**Why Database First?**

| Feature | Benefit |
|---|---|
| **Relational Integrity** | Foreign keys ensure data consistency |
| **Queryability** | Fast SQL queries, indexes, filtering |
| **Scalability** | Multi-user safe, no file locking needed |
| **API-Friendly** | Direct DB access from routers |
| **Transactions** | ACID guarantees, atomic operations |
| **Version History** | Can track edits via timestamps |

**JSON Files as Backup:**

- JSON files (scenarios.json, settings.json, scenario_nodes.json) kept on disk for:
  - Portability/export
  - Version control history
  - Disaster recovery
- **Not used** for API operations (all reads/writes go to DB)
- Migration script loads JSON to DB on first startup

---

## Authentication & Authorization

### JWT Token Flow

```
1. User submits login credentials
   POST /api/v1/login
   { "username": "alon", "password": "secret" }
     ↓
2. Backend verifies credentials (hardcoded for now)
     ↓
3. Generate JWT token
   header = { "alg": "HS256", "typ": "JWT" }
   payload = { "sub": "alon", "exp": <timestamp + 24h> }
   signature = HMAC-SHA256(header.payload, secret)
     ↓
4. Return token to frontend
   { "access_token": "eyJ...", "token_type": "bearer" }
     ↓
5. Frontend stores token (localStorage)
     ↓
6. Frontend includes token in subsequent requests
   Authorization: Bearer eyJ...
     ↓
7. Backend validates token on each request
   - Check signature
   - Check expiration
   - Extract username
     ↓
8. If valid, inject username into handler via Depends()
   If invalid, return 401 Unauthorized
```

### Dependency Injection

FastAPI's `Depends()` pattern automatically:
1. Validates token before handler executes
2. Provides username to handler
3. Returns 401 if token invalid

```python
@router.post("/scenarios")
def save_scenario(
    body: SaveScenarioRequest,
    username: str = Depends(get_current_user),  # ← Automatically injected
    db: Session = Depends(get_db)               # ← Automatically injected
):
    # Handler code runs ONLY if both dependencies succeed
    # username and db are already validated/available
```

### Current Limitation

Passwords are hardcoded (development-only). For production:
- Hash passwords with `bcrypt` or `argon2`
- Store in database
- Compare hashes on login

---

## Database Session Management

### Lifecycle

```
Request arrives
  ↓
Create SQLAlchemy Session (connection to DB)
  ↓
Pass to handler via Depends(get_db)
  ↓
Handler queries/modifies via db.<method>()
  ↓
Handler returns response
  ↓
Session automatically closes
  ↓
Response sent to client
```

### ORM Usage

```python
# Query
profile = db.query(Profile).filter(Profile.id == 1).first()

# Insert
run = SimulationRun(profile_id=1, num_scenarios=0, ...)
db.add(run)
db.commit()  # Explicit commit

# Update
run.num_scenarios = 5
db.commit()

# Delete
db.delete(scenario_result)
db.commit()
```

### Transaction Safety

- `db.commit()` → writes changes to SQLite
- `db.rollback()` → undo uncommitted changes
- If handler raises exception, transaction is rolled back automatically

---

## Error Handling

### Request Validation Errors

```python
# Invalid request body → auto 400 from Pydantic
POST /api/v1/simulate
{ "monthly_income": "not a number" }
# ↓ Returns 400 Bad Request

# Missing required field
POST /api/v1/profiles/1/saved-scenarios
{ "scenario_name": "Test" }  # missing monthly_income
# ↓ Returns 400 Bad Request with detail on missing field
```

### Application Errors

```python
# Profile not found
@router.get("/{profile_id}")
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        # ↓ Returns 404 Not Found

# Duplicate scenario name
if name_exists:
    raise HTTPException(status_code=409, detail="A scenario named '...' already exists.")
    # ↓ Returns 409 Conflict
```

### Unhandled Errors

If a handler raises an exception not caught:
```python
@router.get("/scenarios")
def list_scenarios(db: Session = Depends(get_db)):
    raise ValueError("Unexpected error!")
    # ↓ Caught by FastAPI, returns 500 Internal Server Error
```

---

## Concurrency Model

The backend is designed for concurrent access:

### Stateless Handlers

Each request is independent:
- No shared state between requests
- Handlers don't modify global variables
- Thread-safe (FastAPI runs in thread pool or async)

### Concurrent Saves

Multiple users can save scenarios simultaneously. Database handles concurrency:

```
User A                          User B
save_scenario(name="Plan A")    save_scenario(name="Plan B")
  ↓                                ↓
  BEGIN TRANSACTION               BEGIN TRANSACTION
  INSERT scenario_definitions      Waits (SQLite serializes writers)
  INSERT scenario_events
  INSERT scenario_mortgages
  COMMIT ✓                        ← Can now write
                                  INSERT scenario_definitions
                                  INSERT scenario_events
                                  COMMIT ✓
```

SQLite serializes writes (only one writer at a time) but handles it automatically—no manual locking needed. ACID guarantees ensure both transactions complete fully or roll back completely.

### Database Concurrency

SQLite handles:
- Multiple readers (concurrent GET requests)
- Serialized writers (only one at a time)
- Connection pooling via SQLAlchemy

---

## Historical Returns & Multi-Index Persistence

### How Multi-Index Flows Through the System

The user's choice of which index to use is persisted end-to-end: from UI → API → Database → Storage.

### Request/Response Example: Save NASDAQ Scenario

```
Frontend sends POST /api/v1/profiles/1/saved-scenarios
{
  "scenario_name": "Dot-com Impact",
  "monthly_income": 50000,
  "monthly_expenses": 30000,
  "historical_start_year": 1999,
  "historical_index": "nasdaq",           ← Index choice sent to backend
  "initial_portfolio": 500000,
  "years": 25
}
  ↓
[Pydantic Validation: SaveScenarioRequest]
  - historical_index: Optional[str] field
  - ✓ Validated as string, passed through
  ↓
[Router: whatif_saves.py]
  1. Extract body.historical_index ("nasdaq")
  2. Create Scenario object:
     scenario = Scenario(
       ...,
       historical_index="nasdaq",           ← Passed to domain layer
       historical_start_year=1999
     )
  3. Call simulate(scenario, years=25)
     - Domain layer uses get_historical_rate_sequence(1999, 25, index="nasdaq")
     - Simulates with actual NASDAQ returns 1999-2023
  4. Create ScenarioDefinition:
     definition = ScenarioDefinition(
       ...,
       historical_index="nasdaq",           ← Persisted to database
       historical_start_year=1999
     )
  5. Insert into scenario_definitions table
  ↓
[Database: scenario_definitions table]
  id  | name                | historical_start_year | historical_index | ...
  42  | Dot-com Impact      | 1999                  | nasdaq           | ...
  ↓
[Later: GET /api/v1/scenarios/42]
  1. Query scenario_definitions table
  2. Read: historical_index="nasdaq"
  3. Build WhatIfScenarioSchema:
     schema = WhatIfScenarioSchema(
       ...,
       historical_index="nasdaq"            ← Returned to frontend
     )
  4. Frontend restores exact index choice in UI
```

### Database Schema

The `scenario_definitions` table stores index choice:

```python
class ScenarioDefinition(Base):
    __tablename__ = "scenario_definitions"
    
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    name = Column(String, nullable=False)
    
    # Scenario parameters
    age = Column(Integer, nullable=False)
    initial_portfolio = Column(Float, nullable=False)
    monthly_income = Column(String, nullable=False)      # JSON
    monthly_expenses = Column(String, nullable=False)    # JSON
    currency = Column(String, default="ILS")
    
    # Return rate configuration (mutually exclusive patterns)
    return_rate = Column(Float, nullable=False)              # Fixed % fallback
    historical_start_year = Column(Integer, nullable=True)  # When using historical
    historical_index = Column(String, nullable=True)        # WHICH historical ("sp500"|"nasdaq"|"bonds"|"russell2000")
    
    # Retirement configuration
    withdrawal_rate = Column(Float, nullable=False)
    retirement_mode = Column(String, nullable=False)
    
    # Metadata
    saved_from = Column(String, nullable=False)  # "whatif"
    saved_at = Column(String, nullable=False)    # ISO timestamp
    is_deleted = Column(Boolean, default=False)
```

**Key design:**
- `historical_index` stores the **choice** ("sp500", "nasdaq", etc.)
- The actual return **data** (year → rate) lives immutably in `domain/historical_returns.py`
- Database is thin (stores only what the user chose), code is thick (contains immutable historical data)

### API Contract: Schemas

**WhatIfScenarioSchema** (`schemas.py`) propagates through all Save/Simulate requests:

```python
class WhatIfScenarioSchema(BaseModel):
    # Income/Expenses
    monthly_income: float
    monthly_expenses: float
    
    # Return rate (two modes)
    return_rate: float = 0.07                           # Fixed mode
    historical_start_year: Optional[int] = None         # Historical mode
    historical_index: Optional[str] = None              # Which historical index
    
    # Retirement
    withdrawal_rate: float = 0.04
    retirement_mode: str = "liquid_only"
    
    # Portfolio
    initial_portfolio: float
    starting_age: int
    years: int = 20
    
    # Optional sub-models
    mortgage: Optional[MortgageSchema] = None
    pension: Optional[PensionSchema] = None
    events: list[EventSchema] = Field(default_factory=list)
    
    currency: str = "ILS"
```

**SaveScenarioRequest** / **SimulateRequest** both use this schema for index choice.

### Router Workflow: All Endpoints Pass Index Through

**simulate.py (stateless simulation):**
```python
@router.post("/simulate")
def run_simulation(body: SimulateRequest):
    # SimulateRequest includes historical_index field
    scenario = Scenario(
        ...,
        historical_index=body.historical_index,      # Pass through to domain
        historical_start_year=body.historical_start_year
    )
    result = simulate(scenario, years=body.years)
    return SimulateResponse(...)
```

**whatif_saves.py (persistence):**
```python
@router.post("/{profile_id}/saved-scenarios")
def save_whatif_scenario(profile_id: int, body: SaveScenarioRequest):
    # Two places where historical_index is used:
    
    # 1. Domain simulation
    scenario_obj = Scenario(
        ...,
        historical_index=body.historical_index,      # Simulation uses correct index
        historical_start_year=body.historical_start_year
    )
    sim_result = simulate(scenario_obj, years=body.years)
    
    # 2. Database persistence
    definition = ScenarioDefinition(
        ...,
        historical_index=body.historical_index,      # Store user's choice
        historical_start_year=body.historical_start_year
    )
    db.add(definition)
    db.flush()
    
    # Rest of save logic (events, mortgage, results)...
```

**scenarios.py (retrieval & reconstruction):**
```python
def _build_definition(db: Session, scenario_id: int):
    """Reconstruct exact scenario from database rows."""
    definition = db.query(ScenarioDefinition).filter(
        ScenarioDefinition.id == scenario_id
    ).first()
    
    # Read the persisted index choice
    definition_schema = WhatIfScenarioSchema(
        ...,
        historical_index=definition.historical_index,  # Read from DB
        historical_start_year=definition.historical_start_year
    )
    return definition_schema
```

### Migration: Adding the Column

When deploying to existing databases, an idempotent migration adds the `historical_index` column:

```python
# migration.py
def run_migrations(db):
    # ... previous migrations ...
    
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('scenario_definitions')]
    
    if 'historical_index' not in columns:
        print("  Adding historical_index column to scenario_definitions...")
        db.execute(text("ALTER TABLE scenario_definitions ADD COLUMN historical_index TEXT"))
        db.commit()
```

**Behavior:**
- Old saved scenarios have `historical_index=NULL`
- Retrieving NULL → frontend falls back to "sp500" (default)
- This maintains backward compatibility without needing data migrations

### Error Handling

**Invalid index name:**
```python
# Frontend sends: "historical_index": "vanguard"
# Domain layer validation (historical_returns.py):
if index not in INDICES:
    raise ValueError(f"Unknown index 'vanguard'. Valid: {list(INDICES.keys())}")

# Backend catches:
try:
    result = simulate(scenario, years=body.years)
except ValueError as e:
    raise HTTPException(status_code=422, detail=str(e))
    # → Returns: 422 Unprocessable Entity
```

**Year out of range for index:**
```python
# NASDAQ only has data 1972+
# Request: historical_index="nasdaq", historical_start_year=1970
# Domain validation:
if start_year not in data:
    raise ValueError(f"start_year 1970 out of range for nasdaq (1972–2024)")

# Backend catches:
# → Returns: 422 Unprocessable Entity "start_year 1970 out of range..."
```

### Performance

All database operations remain fast:
- **Column type:** `String` (nullable), no special indexes needed
- **Query time:** Unaffected (text comparison is O(1) for short strings)
- **Storage:** ~5-10 bytes per row (e.g., "nasdaq" is 6 chars)
- **Lookup:** When loading scenario, read is included in existing query (no extra round trips)

### Backward Compatibility

**Old scenarios (before historical_index field):**

| Scenario Created | historical_index in DB | Loaded Behavior |
|---|---|---|
| Before feature | NULL | Frontend defaults to "sp500" |
| After feature | "nasdaq" | Frontend uses "nasdaq" |
| After feature | NULL | Frontend defaults to "sp500" |

**No data migration needed** — the application layer handles NULL gracefully.

---

## Domain Layer Integration

The backend depends on domain layer modules (imported from `domain/`):

```python
# In whatif_saves.py
from domain.models import Scenario, Event
from domain.simulation import simulate
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown
```

### Key Domain Functions

**`simulate(scenario, years=20)`**
- Pure function (no side effects)
- Input: Scenario object
- Output: SimulationResult (year-by-year data)
- Runs in-process on each /simulate or /saved-scenarios request

**`IncomeBreakdown`, `ExpenseBreakdown`**
- Parse income/expenses from flat numbers or component dicts
- Provide `.total` property
- Support deep merge for scenario inheritance

### Calling Domain from Backend

```python
# Build Scenario object from request
scenario_obj = Scenario(
    name="Test",
    monthly_income=IncomeBreakdown({"income": 50000}),
    monthly_expenses=ExpenseBreakdown({"expenses": 30000}),
    return_rate=0.07,
    age=41,
    initial_portfolio=2000000,
    events=[Event(year=5, portfolio_injection=100000, description="Bonus")]
)

# Run simulation
sim_result = simulate(scenario_obj, years=20)

# Use result
for year_data in sim_result.year_data:
    print(f"Year {year_data.year}: Portfolio={year_data.portfolio:,.0f}")
```

---

## Configuration

### Database

```python
# database.py
DATABASE_URL = "sqlite:///./finance_planner.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
```

- File: `finance_planner.db` (created in project root)
- Type: SQLite (simple, single-file, no server needed)
- Thread-safe: `check_same_thread=False` for development

### JWT Secret

```python
# auth.py
SECRET_KEY = "your-secret-key-here"
```

**For production:**
- Move to environment variable: `os.getenv("JWT_SECRET")`
- Use strong random string: `secrets.token_urlsafe(32)`
- Rotate periodically

### CORS

```python
# main.py
CORSMiddleware(
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**For production:**
- Whitelist specific origins (not `["*"]`)
- Specify methods (not `["*"]`)
- Specify headers (not `["*"]`)

---

## Performance Considerations

### Simulation Latency

- `/api/v1/simulate` → runs simulation in-process
- Typical latency: 10-100ms (depends on years simulated)
- Scales linearly with simulation duration

### Database Queries

- `/api/v1/profiles/{id}/runs` → single query, <5ms
- `/api/v1/runs/{id}/scenarios` → single query with join, <5ms
- `/api/v1/scenarios/{id}` → query + load year data, 10-50ms

### File I/O

- Scenarios.json read: 5-20ms (depends on file size, disk speed)
- Scenarios.json write: 5-20ms + file lock wait time
- File lock contention: only between concurrent saves (rare)

### Recommendations

- Cache profiles/scenarios in frontend (don't re-fetch on every interaction)
- Debounce What-If slider changes (don't POST on every pixel movement)
- Use browser's local storage for transient What-If state

---

## Testing Strategy

### Unit Testing

Test individual functions in isolation:
```python
def test_save_scenario():
    # Create test request
    request = SaveScenarioRequest(...)
    
    # Call handler
    response = save_whatif_scenario(1, request, "testuser", db)
    
    # Assert response
    assert response.scenario_result_id > 0
    assert response.retirement_year == 12
```

### Integration Testing

Test full request/response flow:
```python
# Using TestClient
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_login_and_save():
    # Login
    token_response = client.post("/api/v1/login", ...)
    token = token_response.json()["access_token"]
    
    # Save scenario
    save_response = client.post(
        "/api/v1/profiles/1/saved-scenarios",
        headers={"Authorization": f"Bearer {token}"},
        json={...}
    )
    
    assert save_response.status_code == 201
```

### Manual Testing

Use curl or Postman:
```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' | jq -r '.access_token')

# Save scenario
curl -X POST http://localhost:8000/api/v1/profiles/1/saved-scenarios \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}' | jq
```

---

## Extension Points

### Adding a New Endpoint

1. Create new router file in `routers/`
2. Import in `main.py`
3. Register with `app.include_router()`

### Adding Database Model

1. Create class in `models.py`
2. Inherit from `Base`
3. Run `init_db()` to create table

### Adding Validation

1. Create Pydantic model in `schemas.py`
2. Use as parameter in handler
3. FastAPI auto-validates before handler runs

---

## Related Documentation

- [API Reference](API.md) — Endpoint details
- [Backend README](README.md) — Setup and quick start
- [Domain Layer](../../domain/DOMAIN.md) — Simulation engine
