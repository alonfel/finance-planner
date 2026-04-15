import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, SessionLocal
from migration import run_migration
from routers import auth, profiles, scenarios, simulate, whatif_saves, generator, monte_carlo

# Initialize database and run migration
init_db()
db = SessionLocal()
try:
    run_migration(db)
finally:
    db.close()

app = FastAPI(
    title="Finance Planner API",
    description="Backend API for Finance Planner web app",
    version="0.1.0"
)

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(scenarios.router)
app.include_router(simulate.router)
app.include_router(whatif_saves.router)
app.include_router(generator.router)
app.include_router(monte_carlo.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
