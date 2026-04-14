# Finance Planner API Reference

Complete endpoint reference for the Finance Planner backend API.

**Base URL:** `http://localhost:8000`

**API Version:** `v1`

**Authentication:** JWT Bearer token in `Authorization` header

---

## Authentication

### Login

Obtain a JWT access token for authenticated requests.

**Endpoint:** `POST /api/v1/login`

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:**
- `400 Bad Request` — Invalid credentials

**Usage:**
```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' \
  | jq -r '.access_token')

# Use token in subsequent requests
curl http://localhost:8000/api/v1/profiles \
  -H "Authorization: Bearer $TOKEN"
```

---

## Profiles

Retrieve and manage user financial profiles.

### List Profiles

Get all available profiles.

**Endpoint:** `GET /api/v1/profiles`

**Required Auth:** Yes

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "daniel",
    "display_name": "Daniel's Profile",
    "description": "Default financial profile",
    "created_at": "2026-04-01T10:00:00Z"
  },
  {
    "id": 2,
    "name": "alon",
    "display_name": "Alon's Profile",
    "description": "Alon's comprehensive plan",
    "created_at": "2026-04-05T14:30:00Z"
  }
]
```

**Errors:**
- `401 Unauthorized` — Invalid or missing token

---

### Get Profile

Retrieve a specific profile's details.

**Endpoint:** `GET /api/v1/profiles/{profile_id}`

**Required Auth:** Yes

**Path Parameters:**
- `profile_id` (int) — Profile ID

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "daniel",
  "display_name": "Daniel's Profile",
  "description": "Default financial profile",
  "created_at": "2026-04-01T10:00:00Z"
}
```

**Errors:**
- `401 Unauthorized` — Invalid token
- `404 Not Found` — Profile doesn't exist

---

## Scenarios

Retrieve scenario information and results.

### List Simulation Runs

Get all simulation runs for a profile.

**Endpoint:** `GET /api/v1/profiles/{profile_id}/runs`

**Required Auth:** Yes

**Path Parameters:**
- `profile_id` (int) — Profile ID

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "generated_at": "2026-04-10T08:00:00Z",
    "num_scenarios": 3,
    "label": null
  },
  {
    "id": 2,
    "generated_at": "2026-04-12T14:30:00Z",
    "num_scenarios": 5,
    "label": "What-If Saves"
  }
]
```

**Notes:**
- Runs include both pre-simulated scenarios (from analysis/run_simulations.py) and user-saved What-If scenarios
- "What-If Saves" label indicates a run created via the Save Scenario feature

---

### List Scenarios in Run

Get all scenarios belonging to a simulation run.

**Endpoint:** `GET /api/v1/runs/{run_id}/scenarios`

**Required Auth:** Yes

**Path Parameters:**
- `run_id` (int) — Simulation run ID

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "scenario_name": "Baseline",
    "retirement_year": 11,
    "final_portfolio": 18500000
  },
  {
    "id": 2,
    "scenario_name": "Conservative Plan",
    "retirement_year": 15,
    "final_portfolio": 12300000
  }
]
```

---

### Get Scenario Details

Retrieve full scenario data including year-by-year breakdown.

**Endpoint:** `GET /api/v1/scenarios/{scenario_id}`

**Required Auth:** Yes

**Path Parameters:**
- `scenario_id` (int) — Scenario result ID

**Response (200 OK - Fixed Return Rate Scenario):**
```json
{
  "id": 1,
  "scenario_name": "Baseline",
  "retirement_year": 11,
  "definition": {
    "monthly_income": 50000,
    "monthly_expenses": 25000,
    "return_rate": 0.07,
    "starting_age": 41,
    "initial_portfolio": 2000000,
    "withdrawal_rate": 0.04,
    "retirement_mode": "liquid_only",
    "currency": "ILS"
  },
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
    }
    // ... year data continues ...
  ]
}
```

**Response (200 OK - Historical Index Scenario):**
```json
{
  "id": 42,
  "scenario_name": "NASDAQ Dot-com Test",
  "retirement_year": 14,
  "definition": {
    "monthly_income": 45000,
    "monthly_expenses": 25000,
    "historical_start_year": 1999,
    "historical_index": "nasdaq",
    "starting_age": 35,
    "initial_portfolio": 500000,
    "withdrawal_rate": 0.04,
    "retirement_mode": "liquid_only",
    "currency": "ILS"
  },
  "year_data": [
    {
      "year": 1,
      "age": 35,
      "income": 45000,
      "expenses": 25000,
      "net_savings": 20000,
      "portfolio": 520000,
      "required_capital": 500000,
      "mortgage_active": false,
      "pension_value": 0,
      "pension_accessible": false
    }
    // ... year data continues ...
  ]
}
```

**Definition Fields (when present):**
- `monthly_income` — Monthly income in ₪
- `monthly_expenses` — Monthly expenses in ₪
- `return_rate` — Fixed annual return rate (if using fixed mode)
- `historical_start_year` — Start year for historical returns (if using historical mode)
- `historical_index` — Selected index ("sp500", "nasdaq", "bonds", "russell2000") for historical mode
- `starting_age` — Starting age
- `initial_portfolio` — Initial portfolio value
- `withdrawal_rate` — Retirement withdrawal rate
- `retirement_mode` — Retirement validation mode ("liquid_only" or "pension_bridged")
- `currency` — Currency code

**Year Data Fields:**
- `year` — Simulation year (1 = first year)
- `age` — Age at end of year
- `income` — Monthly income (₪)
- `expenses` — Monthly expenses (₪)
- `net_savings` — Monthly income - expenses (₪)
- `portfolio` — Investment portfolio value at year-end (₪)
- `required_capital` — Capital needed to sustain expenses until age 100 (₪)
- `mortgage_active` — Whether mortgage payments are active this year
- `pension_value` — Accumulated pension fund value (₪)
- `pension_accessible` — Whether pension is unlocked and can be used for retirement

---

### Get Scenario Summary

Get high-level summary of a scenario without full year-by-year data.

**Endpoint:** `GET /api/v1/scenarios/{scenario_id}/summary`

**Required Auth:** Yes

**Path Parameters:**
- `scenario_id` (int) — Scenario result ID

**Response (200 OK):**
```json
{
  "scenario_name": "Baseline",
  "retirement_year": 11,
  "final_portfolio": 18500000,
  "years_simulated": 20,
  "retirement_age": 52
}
```

---

## Simulation

Run one-off "What-If" simulations without persisting.

### Simulate Scenario

Execute a single scenario simulation with custom parameters.

**Endpoint:** `POST /api/v1/simulate`

**Required Auth:** No (public endpoint)

**Request (Fixed Return Rate):**
```json
{
  "monthly_income": 50000,
  "monthly_expenses": 25000,
  "return_rate": 0.07,
  "starting_age": 41,
  "initial_portfolio": 2000000,
  "years": 20,
  "events": []
}
```

**Request (Historical Index - S&P 500):**
```json
{
  "monthly_income": 50000,
  "monthly_expenses": 25000,
  "historical_start_year": 1990,
  "historical_index": "sp500",
  "starting_age": 41,
  "initial_portfolio": 2000000,
  "years": 20,
  "events": []
}
```

**Request (Historical Index - NASDAQ Dot-com Crash):**
```json
{
  "monthly_income": 50000,
  "monthly_expenses": 25000,
  "historical_start_year": 1999,
  "historical_index": "nasdaq",
  "starting_age": 41,
  "initial_portfolio": 2000000,
  "years": 25,
  "events": [
    {
      "year": 5,
      "portfolio_injection": 500000,
      "description": "Year 5 bonus"
    }
  ]
}
```

**Request Fields:**
- `monthly_income` (float) — Monthly income in ₪
- `monthly_expenses` (float) — Monthly expenses in ₪
- **Fixed return mode (mutually exclusive with historical):**
  - `return_rate` (float) — Annual investment return rate (0.07 = 7%)
- **Historical return mode (mutually exclusive with fixed):**
  - `historical_start_year` (int) — Starting year for historical data lookup (e.g., 1990)
  - `historical_index` (string, optional) — Which index to use: `"sp500"` | `"nasdaq"` | `"bonds"` | `"russell2000"`. Defaults to `"sp500"` if not specified.
- `starting_age` (int) — Current age
- `initial_portfolio` (float) — Starting investment portfolio in ₪
- `years` (int, default: 20) — Number of years to simulate
- `events` (array, default: []) — One-time portfolio changes (see Event schema below)

**Historical Index Details:**

| Index | Years | Description |
|---|---|---|
| `"sp500"` | 1928–2024 | S&P 500 large-cap US equities (default) |
| `"nasdaq"` | 1972–2024 | NASDAQ Composite tech-heavy index |
| `"bonds"` | 1928–2024 | US 10-Year Treasury fixed income |
| `"russell2000"` | 1979–2024 | Russell 2000 small-cap US equities |

**Note on historical return rates:**
- When `historical_start_year` is provided, the API uses actual annual returns from the selected index for each simulation year
- If simulation exceeds available data for an index, years wrap deterministically from that index's start year (e.g., NASDAQ 1972+)
- `historical_index` is ignored if `historical_start_year` is not provided (falls back to `return_rate`)
- Invalid `historical_index` values return `422 Unprocessable Entity`
- `historical_start_year` values before the index's minimum year return `422 Unprocessable Entity`

**Event Schema:**
- `year` (int) — Simulation year (1-indexed)
- `portfolio_injection` (float) — Amount to add (positive) or subtract (negative) from portfolio (₪)
- `description` (string) — Human-readable label for the event

**Response (200 OK):**
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
    }
    // ... year data continues ...
  ]
}
```

**Response Fields:**
- `scenario_name` — "What-If Simulation"
- `retirement_year` — Year in which portfolio can sustain living expenses (null if doesn't achieve)
- `final_portfolio` — Portfolio value at end of simulation (₪)
- `total_savings` — Total amount saved over simulation period (₪)
- `year_data` — Year-by-year breakdown (see Year Data Fields above)

**Errors:**
- `400 Bad Request` — Invalid parameters (negative values, invalid age, etc.)

**Example Usage:**
```bash
curl -X POST http://localhost:8000/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "monthly_income": 60000,
    "monthly_expenses": 30000,
    "return_rate": 0.07,
    "starting_age": 35,
    "initial_portfolio": 1500000,
    "years": 25,
    "events": [
      {
        "year": 10,
        "portfolio_injection": 1000000,
        "description": "Property sale proceeds"
      }
    ]
  }' | jq
```

---

## What-If Saves

Save user-created What-If scenarios to persist them as named scenarios.

### Save What-If Scenario

Persist a What-If scenario configuration as a named scenario. The scenario is:
1. Simulated in-process
2. Inserted into the `scenario_definitions` table in SQLite
3. Recorded in SQLite under the "What-If Saves" simulation run

**Endpoint:** `POST /api/v1/profiles/{profile_id}/saved-scenarios`

**Required Auth:** Yes

**Path Parameters:**
- `profile_id` (int) — Profile ID

**Request (Fixed Return):**
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

**Request (Historical Index):**
```json
{
  "scenario_name": "NASDAQ Dot-com Test",
  "monthly_income": 45000,
  "monthly_expenses": 25000,
  "historical_start_year": 1999,
  "historical_index": "nasdaq",
  "starting_age": 35,
  "initial_portfolio": 500000,
  "years": 25,
  "events": [
    {
      "year": 5,
      "portfolio_injection": 250000,
      "description": "Anticipated bonus"
    }
  ]
}
```

**Request Fields:**
- `scenario_name` (string, 1-100 chars) — **Unique** name for the scenario (will fail if name already exists)
- `monthly_income` (float) — Monthly income in ₪
- `monthly_expenses` (float) — Monthly expenses in ₪
- **Fixed return mode (choose one approach):**
  - `return_rate` (float, default: 0.07) — Annual investment return rate
- **Historical return mode (choose one approach):**
  - `historical_start_year` (int) — Starting year for historical data
  - `historical_index` (string, optional) — Index to use: `"sp500"` | `"nasdaq"` | `"bonds"` | `"russell2000"`. Defaults to `"sp500"`.
- `starting_age` (int) — Current age
- `initial_portfolio` (float) — Starting investment portfolio in ₪
- `years` (int, default: 20) — Simulation period
- `events` (array, default: []) — One-time portfolio adjustments
- `withdrawal_rate` (float, optional, default: 0.04) — Retirement withdrawal rate (4% rule)
- `retirement_mode` (string, optional, default: "liquid_only") — Retirement validation mode
- `mortgage` (object, optional) — Mortgage details (if applicable)
- `pension` (object, optional) — Pension details (if applicable)
- `currency` (string, optional, default: "ILS") — Currency code

**Historical Index Details (see Simulate endpoint above for complete reference)**

**Response (201 Created):**
```json
{
  "scenario_result_id": 42,
  "run_id": 2,
  "scenario_name": "Conservative Plan",
  "retirement_year": 12,
  "final_portfolio": 17500000
}
```

**Response Fields:**
- `scenario_result_id` — ID of the new ScenarioResult in SQLite
- `run_id` — ID of the "What-If Saves" SimulationRun
- `scenario_name` — Echoed scenario name
- `retirement_year` — Year in which retirement is achievable (null if not)
- `final_portfolio` — Portfolio value at simulation end

**Errors:**
- `401 Unauthorized` — Missing or invalid token
- `404 Not Found` — Profile doesn't exist
- `409 Conflict` — Scenario name already exists

**Conflict Response (409):**
```json
{
  "detail": "A scenario named 'Conservative Plan' already exists."
}
```

**Example Usage:**
```bash
PROFILE_ID=1
TOKEN="your-jwt-token-here"

curl -X POST http://localhost:8000/api/v1/profiles/$PROFILE_ID/saved-scenarios \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_name": "My Custom Plan",
    "monthly_income": 55000,
    "monthly_expenses": 25000,
    "return_rate": 0.07,
    "starting_age": 42,
    "initial_portfolio": 2500000,
    "years": 20,
    "events": []
  }' | jq
```

**What Happens After Save:**

1. **Database** — New records created in SQLite:
   - `scenario_definitions` — Scenario definition with `saved_from='whatif'` marker and timestamp
   - `scenario_events` — One-time events (if any) linked via `scenario_id` FK
   - `scenario_mortgages` — Optional mortgage (if present) linked via `scenario_id` FK
   - Get-or-create "What-If Saves" `SimulationRun` (one per profile for grouping)
   - `ScenarioResult` — Links definition to simulation results via `scenario_id` FK
   - `YearData` — Year-by-year simulation results (one per simulated year)

2. **JSON Backup** — Optional export to `data/profiles/{profile_name}/scenarios.json` for portability

3. **UI** — Scenario immediately available in Scenarios list
   - Under "What-If Saves" run
   - Can be selected and viewed like any other scenario
   - Can be used as parent for scenario inheritance (ScenarioNode)

---

## Health Check

### Server Status

Basic health check to verify server is running.

**Endpoint:** `GET /health`

**Required Auth:** No

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

---

## Error Handling

All error responses follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| `200` | OK | Successful GET request |
| `201` | Created | Scenario saved successfully |
| `400` | Bad Request | Invalid parameters (negative income, etc.) |
| `401` | Unauthorized | Missing or invalid token |
| `404` | Not Found | Profile/scenario/run doesn't exist |
| `409` | Conflict | Duplicate scenario name |
| `500` | Internal Server Error | Unexpected backend error |

---

## Rate Limiting

No rate limiting implemented. For production, add rate limiting middleware.

---

## CORS

**Allowed Origins (Development):**
- `http://localhost:5173`
- `http://127.0.0.1:5173`

**Allowed Methods:** GET, POST, PUT, DELETE, OPTIONS

**Allowed Headers:** Content-Type, Authorization

Update `main.py` for production domains.

---

## Pagination

Not yet implemented. All list endpoints return full results.

---

## Versioning

API is versioned via URL prefix (`/api/v1/`). Future versions will use `/api/v2/`, etc.

---

## Related Documentation

- [Backend README](README.md) — Setup and quick start
- [Backend Architecture](ARCHITECTURE.md) — Design patterns and data flow
- [Features Guide](../FEATURES.md) — User-facing feature documentation
