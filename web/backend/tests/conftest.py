"""Pytest configuration and fixtures for backend tests."""
import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime
import importlib.util

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), "..")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Add root directory to path
root_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..")
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

import database as db_module
from models import User, Profile, SimulationRun, ScenarioResult, YearData
from auth import create_access_token

# Import app from backend main
backend_main_path = os.path.join(backend_dir, "main.py")
spec = importlib.util.spec_from_file_location("backend_main", backend_main_path)
backend_main_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend_main_module)
app = backend_main_module.app


@pytest.fixture
def test_db():
    """Create file-based SQLite database for each test."""
    # Create a temporary directory for the test database
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )
    db_module.Base.metadata.create_all(bind=engine)
    yield engine

    # Cleanup
    try:
        os.remove(db_path)
        os.rmdir(tmpdir)
    except Exception:
        pass


@pytest.fixture
def db_session(test_db):
    """Create a new database session for each test."""
    TestingSessionLocal = sessionmaker(bind=test_db, expire_on_commit=False)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(db_session, monkeypatch):
    """Create test client with mocked database dependency."""
    def override_get_db():
        yield db_session

    from database import get_db
    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        username="testuser",
        password_hash="$2b$12$gSvqqUPHyo8uvqezjYlMyeIYnzV2J3hO3Z.Ks7w8sxE.x8uqQZv.W"  # "password" hashed
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_profile(db_session, tmp_path, monkeypatch):
    """Create a test profile with mocked scenarios.json path."""
    profile = Profile(
        id=1,
        name="test_profile",
        display_name="Test Profile",
        description="Test profile for unit tests",
        created_at=datetime.utcnow().isoformat()
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    # Create scenarios.json in temp directory
    scenarios_file = tmp_path / "scenarios.json"
    scenarios_file.write_text(json.dumps({
        "profile_name": "test_profile",
        "currency": "ILS",
        "scenarios": []
    }, indent=2))

    # Monkeypatch get_scenarios_path to use our temp file
    def mock_get_scenarios_path(profile_name):
        if profile_name == "test_profile":
            return scenarios_file
        return Path(f"/tmp/{profile_name}/scenarios.json")

    monkeypatch.setattr("routers.whatif_saves.get_scenarios_path", mock_get_scenarios_path)
    monkeypatch.setattr("infrastructure.data_layer.get_scenarios_path", mock_get_scenarios_path)

    return profile, scenarios_file


@pytest.fixture
def auth_token(test_user):
    """Create a valid JWT token for testing."""
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture
def authorized_client(client, auth_token):
    """Return test client with authorization header."""
    client.headers = {"Authorization": f"Bearer {auth_token}"}
    return client


@pytest.fixture
def test_simulation_run(db_session, test_profile):
    """Create a test simulation run."""
    profile, _ = test_profile
    run = SimulationRun(
        profile_id=profile.id,
        generated_at=datetime.utcnow().isoformat(),
        num_scenarios=0,
        label="Test Run"
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


@pytest.fixture
def test_scenario(db_session, test_simulation_run):
    """Create a test scenario with year data."""
    scenario = ScenarioResult(
        run_id=test_simulation_run.id,
        scenario_name="Test Scenario",
        retirement_year=15
    )
    db_session.add(scenario)
    db_session.flush()

    # Add year data
    for year in range(1, 21):
        year_data = YearData(
            result_id=scenario.id,
            year=year,
            age=40 + year,
            income=50000,
            expenses=25000,
            net_savings=25000,
            portfolio=1000000 * (1.07 ** year),
            required_capital=500000,
            mortgage_active=False,
            pension_value=0,
            pension_accessible=False
        )
        db_session.add(year_data)

    db_session.commit()
    db_session.refresh(scenario)
    return scenario
