# Finance Planner Web App — Quick Start

🎉 **Your financial simulation engine is now a web app!**

## What Was Built

A complete MVP web application for viewing and analyzing financial simulations:

- **Backend API** (FastAPI + SQLite)
  - JWT authentication
  - RESTful endpoints for profiles, scenarios, and simulation results
  - Database seeded with your Alon profile's 3 scenarios

- **Frontend UI** (Vue 3 + Chart.js)
  - Clean, responsive design
  - Login screen
  - Profile dashboard
  - Scenarios list with run selector
  - Detailed scenario view with:
    - Portfolio growth chart
    - Year-by-year analysis table
    - Retirement timing and metrics

## Start the App (Already Running)

Both servers are currently running. Open your browser:

### 🌐 Frontend
**http://localhost:5173**

### 📊 Backend API
**http://localhost:8000**  
API docs (Swagger): **http://localhost:8000/docs**

## Login Credentials

```
Username: alon
Password: alon123
```

## What You Can Do Now

1. **View your profiles** — Dashboard shows Alon profile with pension modeling
2. **Explore scenarios** — 3 scenarios already simulated:
   - Alon - Baseline (retires Year 11)
   - Alon - IPO Year 2 (retires Year 6)
   - Alon - IPO Year 3 (retires Year 5)
3. **Analyze results** — Each scenario shows:
   - Portfolio growth chart (portfolio vs required capital)
   - Pension accumulation (tracked separately)
   - Year-by-year income, expenses, savings, portfolio
   - Retirement year and retirement age

## File Structure

```
finance_planner/
└── web/
    ├── backend/
    │   ├── main.py              # FastAPI app
    │   ├── models.py            # SQLAlchemy models
    │   ├── database.py          # SQLite setup
    │   ├── auth.py              # JWT + password hashing
    │   ├── seed.py              # Database seeding
    │   ├── routers/             # API endpoints
    │   └── requirements.txt
    ├── frontend/
    │   ├── src/
    │   │   ├── views/           # Page components
    │   │   ├── components/      # Reusable components
    │   │   ├── stores/          # Pinia state (auth)
    │   │   ├── router/          # Vue Router
    │   │   └── App.vue
    │   ├── package.json
    │   ├── vite.config.js
    │   └── index.html
    ├── README.md                # Full documentation
    └── data/
        └── finance_planner.db   # SQLite database
```

## Next Steps (Future Phases)

### Phase 1: Input Forms
- [ ] Create/edit scenarios in the UI
- [ ] Add income and expense breakdowns
- [ ] Define mortgage and pension settings
- [ ] Support scenario inheritance (parent/child relationships)

### Phase 2: Israeli Defaults Layer
- [ ] Profile template system
- [ ] Pre-populated defaults by user type
- [ ] Tax assumptions and pension parameters
- [ ] Quick setup wizard for new users

### Phase 3: Multi-User & Sharing
- [ ] User registration
- [ ] Save multiple scenario plans per user
- [ ] Share scenarios with friends/family
- [ ] Scenario comparison views
- [ ] Export to PDF/Excel

### Phase 4: AI Insights
- [ ] Generate narrative analysis (like reports)
- [ ] Chatbot for answering "what-if" questions
- [ ] Optimization suggestions
- [ ] Risk analysis

## Architecture Decisions Made

1. **SQLite** — Simple, no server needed, works great for MVP
2. **FastAPI** — Modern Python framework, auto-generated API docs
3. **Vue 3 Composition API** — Flexible, lightweight frontend
4. **Chart.js** — Proven charting library, works well with Vue
5. **JWT auth** — Stateless, scales well, frontend-friendly
6. **Backwards compatible** — New web app doesn't affect existing Python CLI

## Database Schema

The MVP uses a focused schema for displaying cached results:

- `users` — Login credentials (seeded with alon)
- `profiles` — User profiles (maps to existing data/profiles/{name}/)
- `simulation_runs` — Cached simulation batches
- `scenario_results` — One per scenario per run
- `year_data` — Year-by-year simulation output

Future phases will add tables for scenario definitions (income, expenses, mortgage, events).

## API Endpoints

All authenticated with Bearer JWT token:

```
POST   /api/v1/auth/login                    Login
GET    /api/v1/profiles                      List profiles
GET    /api/v1/profiles/:profileId/runs      List simulation runs
GET    /api/v1/runs/:runId/scenarios         List scenarios in a run
GET    /api/v1/scenarios/:resultId           Full scenario with year data
GET    /api/v1/scenarios/:resultId/summary   Scenario summary metrics
```

## Troubleshooting

**Servers not responding?**
```bash
# Check backend
curl http://localhost:8000/health

# Check frontend build
cat /tmp/frontend.log | tail -10

# Check backend logs
cat /tmp/backend.log | tail -10
```

**Database issues?**
```bash
# Verify it exists
ls -la data/finance_planner.db

# Re-seed if needed
python web/backend/seed.py
```

**Port conflicts?**
```bash
# Check what's using 8000 or 5173
lsof -i :8000
lsof -i :5173

# Kill if needed
kill -9 <PID>
```

## Key Design Principles

✅ **Output-first design** — Built from simulation results backward  
✅ **Configuration-driven** — Load data from existing cache  
✅ **Simple but extensible** — MVP has clean architecture for growth  
✅ **Israeli-specific** — Defaults, currency (₪), and pension modeling  
✅ **User-centric** — Clean UI, clear metrics, intuitive flow  

## Technical Stack Summary

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | FastAPI | Modern, fast, auto-docs |
| Database | SQLite | Simple, no ops, ACID |
| Frontend | Vue 3 | Lightweight, flexible |
| Charts | Chart.js | Proven, lightweight |
| Auth | JWT | Stateless, scalable |
| Build | Vite | Fast, modern |

## What's Working

✅ Login and authentication  
✅ Profile listing  
✅ Simulation run selection  
✅ Scenario browsing  
✅ Portfolio growth visualization  
✅ Year-by-year data display  
✅ Retirement year highlighting  
✅ Currency formatting (₪)  
✅ Pension tracking  
✅ Responsive cards and tables  

## Known Limitations (By Design for MVP)

- Single user (alon) hardcoded
- No input forms (view-only mode)
- Desktop layout only
- No scenario editing
- No user registration
- No multi-profile support in UI
- No AI insights yet

These are all planned for future phases.

---

**Happy analyzing! 📈**

Questions? Check `web/README.md` for full documentation or explore `web/backend/main.py` for the API implementation.
