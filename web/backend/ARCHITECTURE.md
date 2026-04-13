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
  2. Check scenario name is unique → read scenarios.json
  3. Create Scenario object from request params
  4. Call simulate() from domain layer → run simulation
  5. Append to scenarios.json with file lock → atomic write
  6. Get-or-create "What-If Saves" SimulationRun
  7. Insert ScenarioResult + YearData rows into SQLite
  8. Commit transaction
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

When a user saves a What-If scenario, data flows to two persistence layers:

### 1. Disk Persistence (scenarios.json)

```
AppendToScenarioJson()
  ↓
  1. Acquire file lock (scenarios.json.lock)
  2. Read current scenarios.json
  3. Parse JSON to dict
  4. Append new scenario to "scenarios" array
  5. Add metadata:
     - "saved_from": "whatif"
     - "saved_at": ISO timestamp
  6. Write JSON back to disk
  7. Release lock
  ↓
Result: Scenario now in version-controlled, human-readable file
```

**File Lock Strategy:**
- Uses `filelock.FileLock()` for safe concurrent access
- Timeout: 5 seconds (prevents deadlock)
- Ensures only one writer at a time
- Read operation is atomic (JSON parsing happens in-memory)

**Why File Lock?**
- Multiple frontend users might save simultaneously
- Without locking, writes could corrupt the file
- With locking, writes are serialized and safe

**Location:** `data/profiles/{profile_name}/scenarios.json`

**Example Entry:**
```json
{
  "name": "Conservative Plan",
  "monthly_income": 50000,
  "monthly_expenses": 20000,
  "return_rate": 0.06,
  "age": 41,
  "initial_portfolio": 2000000,
  "currency": "ILS",
  "events": [
    {
      "year": 5,
      "portfolio_injection": 250000,
      "description": "Bonus"
    }
  ],
  "saved_from": "whatif",
  "saved_at": "2026-04-13T14:30:00Z"
}
```

### 2. Database Persistence (SQLite)

```
SaveToDatabase()
  ↓
  1. Get-or-create "What-If Saves" SimulationRun
     - Query: SimulationRun where profile_id=1 and label="What-If Saves"
     - If exists: reuse
     - If not: create new record
  ↓
  2. Insert ScenarioResult
     - run_id = (from step 1)
     - scenario_name = "Conservative Plan"
     - retirement_year = (from simulation)
  ↓
  3. Insert YearData rows (one per simulated year)
     - result_id = (from step 2)
     - year, age, income, expenses, portfolio, ...
  ↓
  4. Update SimulationRun.num_scenarios
     - Count all ScenarioResult rows for this run
  ↓
  5. Commit transaction
  ↓
Result: Scenario queryable via REST API endpoints
```

**Schema:**

```
SimulationRun
├── id (PK)
├── profile_id (FK)
├── generated_at (timestamp)
├── num_scenarios (count of scenarios in run)
└── label (optional, "What-If Saves" for user saves)
     ↓
     ├── ScenarioResult (many)
     │  ├── id (PK)
     │  ├── run_id (FK)
     │  ├── scenario_name
     │  ├── retirement_year
     │  └── YearData (many)
     │     ├── result_id (FK)
     │     ├── year
     │     ├── age
     │     ├── portfolio
     │     └── ... (15+ fields)
```

**Why Both Disk and DB?**

| | Disk (scenarios.json) | Database (SQLite) |
|---|---|---|
| **Purpose** | Version control, human-readable | Queryable, indexed, relational |
| **Latency** | File I/O (~10ms) | DB query (~5ms) |
| **Durability** | Git-tracked, backed up | ACID guarantees |
| **Query Ability** | Grep/text search only | SQL queries, indexes |
| **Data Loading** | Load once at app start | Lazy-loaded on demand |
| **Use Case** | Archive, config management | Real-time API access |

**Sync Points:**
- Both written atomically (within same handler)
- Disk writes happen before DB to preserve JSON integrity
- If DB insert fails, scenarios.json is already written (slightly inconsistent but safe)
- Next restart will load scenarios.json, re-sync DB

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

Multiple users can save scenarios simultaneously:

```
User A                          User B
save_scenario(name="Plan A")    save_scenario(name="Plan B")
  ↓                                ↓
  Acquire lock                    Waits for lock
  Read scenarios.json
  Append Plan A
  Write back
  Release lock                    ← Can now acquire
                                  Read scenarios.json
                                  Append Plan B
                                  Write back
                                  Release lock
```

With file locking, writes don't corrupt each other.

### Database Concurrency

SQLite handles:
- Multiple readers (concurrent GET requests)
- Serialized writers (only one at a time)
- Connection pooling via SQLAlchemy

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
