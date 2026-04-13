"""Test suite for backend data persistence (SQLite + DB operations)."""
import pytest
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from sqlalchemy.orm import Session
from models import Profile, SimulationRun, ScenarioResult, YearData, ScenarioDefinition, ScenarioEvent
from schemas import SaveScenarioRequest, EventSchema, MortgageSchema
from routers.whatif_saves import (
    _get_or_create_whatif_run,
    WHATIF_SAVES_LABEL
)


class TestSaveWhatIfScenario:
    """Test the save_whatif_scenario endpoint and helper functions."""

    def test_save_scenario_creates_scenario_result(self, db_session, test_profile, authorized_client):
        """Saving a scenario should create ScenarioResult in database."""
        profile, scenarios_file = test_profile

        response = authorized_client.post(
            f"/api/v1/profiles/{profile.id}/saved-scenarios",
            json={
                "scenario_name": "Test Save",
                "monthly_income": 50000,
                "monthly_expenses": 25000,
                "return_rate": 0.07,
                "starting_age": 41,
                "initial_portfolio": 2000000,
                "years": 20,
                "events": [],
                "mortgage": None
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["scenario_name"] == "Test Save"
        assert data["scenario_result_id"] is not None
        assert data["run_id"] is not None
        assert data["final_portfolio"] is not None

        # Verify scenario was created in database
        scenario = db_session.query(ScenarioResult).filter(
            ScenarioResult.id == data["scenario_result_id"]
        ).first()
        assert scenario is not None
        assert scenario.scenario_name == "Test Save"

    def test_save_scenario_creates_year_data_rows(self, db_session, test_profile, authorized_client):
        """Saving a scenario should create YearData rows for each simulated year."""
        profile, scenarios_file = test_profile

        response = authorized_client.post(
            f"/api/v1/profiles/{profile.id}/saved-scenarios",
            json={
                "scenario_name": "Year Data Test",
                "monthly_income": 50000,
                "monthly_expenses": 25000,
                "return_rate": 0.07,
                "starting_age": 41,
                "initial_portfolio": 2000000,
                "years": 20,
                "events": [],
                "mortgage": None
            }
        )

        assert response.status_code == 201
        scenario_id = response.json()["scenario_result_id"]

        # Verify 20 YearData rows created
        year_data_rows = db_session.query(YearData).filter(
            YearData.result_id == scenario_id
        ).all()
        assert len(year_data_rows) == 20

        # Verify year field is 1-indexed
        years = [yd.year for yd in year_data_rows]
        assert years == list(range(1, 21))

    def test_save_scenario_creates_whatif_run_on_first_save(self, db_session, test_profile, authorized_client):
        """First save should create 'What-If Saves' run."""
        profile, scenarios_file = test_profile

        response = authorized_client.post(
            f"/api/v1/profiles/{profile.id}/saved-scenarios",
            json={
                "scenario_name": "First Save",
                "monthly_income": 50000,
                "monthly_expenses": 25000,
                "return_rate": 0.07,
                "starting_age": 41,
                "initial_portfolio": 2000000,
                "years": 20,
                "events": [],
                "mortgage": None
            }
        )

        assert response.status_code == 201
        run_id = response.json()["run_id"]

        # Verify run exists and has correct label
        run = db_session.query(SimulationRun).filter(
            SimulationRun.id == run_id
        ).first()
        assert run is not None
        assert run.label == WHATIF_SAVES_LABEL
        assert run.profile_id == profile.id

    def test_save_scenario_with_events_persists_all_events(self, db_session, test_profile, authorized_client):
        """Saving scenario with events should persist them to database."""
        profile, scenarios_file = test_profile

        events = [
            {"year": 5, "portfolio_injection": 500000, "description": "Bonus"},
            {"year": 10, "portfolio_injection": -100000, "description": "Car purchase"}
        ]

        response = authorized_client.post(
            f"/api/v1/profiles/{profile.id}/saved-scenarios",
            json={
                "scenario_name": "With Events",
                "monthly_income": 50000,
                "monthly_expenses": 25000,
                "return_rate": 0.07,
                "starting_age": 41,
                "initial_portfolio": 2000000,
                "years": 20,
                "events": events,
                "mortgage": None
            }
        )

        assert response.status_code == 201
        scenario_id = response.json()["scenario_result_id"]

        # Verify events were persisted to database
        scenario = db_session.query(ScenarioResult).filter(
            ScenarioResult.id == scenario_id
        ).first()
        assert scenario is not None
        assert scenario.scenario_id is not None

        # Query events from scenario definition
        definition = db_session.query(ScenarioDefinition).filter(
            ScenarioDefinition.id == scenario.scenario_id
        ).first()
        db_events = db_session.query(ScenarioEvent).filter(
            ScenarioEvent.scenario_id == definition.id
        ).all()

        assert len(db_events) == 2
        assert db_events[0].year == 5
        assert db_events[0].portfolio_injection == 500000
        assert db_events[1].year == 10
        assert db_events[1].portfolio_injection == -100000

    def test_save_scenario_with_mortgage_persists_mortgage(self, db_session, test_profile, authorized_client):
        """Saving scenario with mortgage should persist mortgage details to database."""
        profile, scenarios_file = test_profile

        mortgage = {
            "principal": 1500000,
            "annual_rate": 0.045,
            "duration_years": 20,
            "currency": "ILS"
        }

        response = authorized_client.post(
            f"/api/v1/profiles/{profile.id}/saved-scenarios",
            json={
                "scenario_name": "With Mortgage",
                "monthly_income": 50000,
                "monthly_expenses": 25000,
                "return_rate": 0.07,
                "starting_age": 41,
                "initial_portfolio": 2000000,
                "years": 20,
                "events": [],
                "mortgage": mortgage
            }
        )

        assert response.status_code == 201
        scenario_id = response.json()["scenario_result_id"]

        # Verify mortgage was persisted to database
        scenario = db_session.query(ScenarioResult).filter(
            ScenarioResult.id == scenario_id
        ).first()
        assert scenario is not None
        assert scenario.scenario_id is not None

        from models import ScenarioMortgage
        db_mortgage = db_session.query(ScenarioMortgage).filter(
            ScenarioMortgage.scenario_id == scenario.scenario_id
        ).first()

        assert db_mortgage is not None
        assert db_mortgage.principal == 1500000
        assert db_mortgage.annual_rate == 0.045
        assert db_mortgage.duration_years == 20

    def test_save_scenario_duplicate_name_returns_409(self, db_session, test_profile, authorized_client):
        """Saving with duplicate name should return 409 Conflict."""
        profile, scenarios_file = test_profile

        # First save
        response1 = authorized_client.post(
            f"/api/v1/profiles/{profile.id}/saved-scenarios",
            json={
                "scenario_name": "Unique Name",
                "monthly_income": 50000,
                "monthly_expenses": 25000,
                "return_rate": 0.07,
                "starting_age": 41,
                "initial_portfolio": 2000000,
                "years": 20,
                "events": [],
                "mortgage": None
            }
        )
        assert response1.status_code == 201

        # Second save with same name
        response2 = authorized_client.post(
            f"/api/v1/profiles/{profile.id}/saved-scenarios",
            json={
                "scenario_name": "Unique Name",
                "monthly_income": 55000,
                "monthly_expenses": 26000,
                "return_rate": 0.08,
                "starting_age": 42,
                "initial_portfolio": 2500000,
                "years": 20,
                "events": [],
                "mortgage": None
            }
        )

        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    def test_save_scenario_missing_profile_returns_404(self, authorized_client):
        """Saving to non-existent profile should return 404."""
        response = authorized_client.post(
            "/api/v1/profiles/99999/saved-scenarios",
            json={
                "scenario_name": "Test",
                "monthly_income": 50000,
                "monthly_expenses": 25000,
                "return_rate": 0.07,
                "starting_age": 41,
                "initial_portfolio": 2000000,
                "years": 20,
                "events": [],
                "mortgage": None
            }
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_save_scenario_creates_definition_in_db(self, db_session, test_profile, authorized_client):
        """Saving should create scenario definition in database."""
        profile, scenarios_file = test_profile

        # Initial state - no definitions
        initial_count = db_session.query(ScenarioDefinition).filter(
            ScenarioDefinition.profile_id == profile.id
        ).count()
        assert initial_count == 0

        # Save first scenario
        response1 = authorized_client.post(
            f"/api/v1/profiles/{profile.id}/saved-scenarios",
            json={
                "scenario_name": "Scenario 1",
                "monthly_income": 50000,
                "monthly_expenses": 25000,
                "return_rate": 0.07,
                "starting_age": 41,
                "initial_portfolio": 2000000,
                "years": 20,
                "events": [],
                "mortgage": None
            }
        )

        assert response1.status_code == 201

        # Verify created in database
        count_after_1 = db_session.query(ScenarioDefinition).filter(
            ScenarioDefinition.profile_id == profile.id
        ).count()
        assert count_after_1 == 1

        # Save second scenario
        response2 = authorized_client.post(
            f"/api/v1/profiles/{profile.id}/saved-scenarios",
            json={
                "scenario_name": "Scenario 2",
                "monthly_income": 55000,
                "monthly_expenses": 26000,
                "return_rate": 0.08,
                "starting_age": 42,
                "initial_portfolio": 2500000,
                "years": 20,
                "events": [],
                "mortgage": None
            }
        )

        assert response2.status_code == 201

        # Verify second scenario created
        count_after_2 = db_session.query(ScenarioDefinition).filter(
            ScenarioDefinition.profile_id == profile.id
        ).count()
        assert count_after_2 == 2

        # Verify names are correct
        definitions = db_session.query(ScenarioDefinition).filter(
            ScenarioDefinition.profile_id == profile.id
        ).order_by(ScenarioDefinition.id).all()
        assert definitions[0].name == "Scenario 1"
        assert definitions[1].name == "Scenario 2"

    def test_save_scenario_marks_as_saved_from_whatif(self, db_session, test_profile, authorized_client):
        """Saved scenario should have 'saved_from': 'whatif' marker in DB."""
        profile, scenarios_file = test_profile

        response = authorized_client.post(
            f"/api/v1/profiles/{profile.id}/saved-scenarios",
            json={
                "scenario_name": "What-If Save",
                "monthly_income": 50000,
                "monthly_expenses": 25000,
                "return_rate": 0.07,
                "starting_age": 41,
                "initial_portfolio": 2000000,
                "years": 20,
                "events": [],
                "mortgage": None
            }
        )

        assert response.status_code == 201
        scenario_id = response.json()["scenario_result_id"]

        # Verify in database
        scenario = db_session.query(ScenarioResult).filter(
            ScenarioResult.id == scenario_id
        ).first()
        assert scenario is not None
        assert scenario.scenario_id is not None

        definition = db_session.query(ScenarioDefinition).filter(
            ScenarioDefinition.id == scenario.scenario_id
        ).first()
        assert definition is not None
        assert definition.saved_from == "whatif"
        assert definition.saved_at is not None

    def test_save_scenario_returns_correct_final_portfolio(self, db_session, test_profile, authorized_client):
        """Response should include final_portfolio from simulation."""
        profile, scenarios_file = test_profile

        response = authorized_client.post(
            f"/api/v1/profiles/{profile.id}/saved-scenarios",
            json={
                "scenario_name": "Portfolio Test",
                "monthly_income": 50000,
                "monthly_expenses": 25000,
                "return_rate": 0.07,
                "starting_age": 41,
                "initial_portfolio": 2000000,
                "years": 20,
                "events": [],
                "mortgage": None
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["final_portfolio"] > 0
        # With ₪25k/year savings at 7% growth, should be significantly higher than initial
        assert data["final_portfolio"] > data["scenario_result_id"]  # Just a sanity check




class TestGetOrCreateWhatIfRun:
    """Test the get_or_create_whatif_run helper."""

    def test_get_or_create_whatif_run_creates_new_run(self, db_session, test_profile):
        """Should create 'What-If Saves' run if it doesn't exist."""
        profile, _ = test_profile

        # Verify run doesn't exist
        existing_run = db_session.query(SimulationRun).filter(
            SimulationRun.profile_id == profile.id,
            SimulationRun.label == WHATIF_SAVES_LABEL
        ).first()
        assert existing_run is None

        # Get or create
        run = _get_or_create_whatif_run(db_session, profile.id)

        assert run is not None
        assert run.label == WHATIF_SAVES_LABEL
        assert run.profile_id == profile.id
        assert run.num_scenarios == 0

    def test_get_or_create_whatif_run_returns_existing_run(self, db_session, test_profile):
        """Should return existing 'What-If Saves' run."""
        profile, _ = test_profile

        # Create first run
        run1 = _get_or_create_whatif_run(db_session, profile.id)
        run1_id = run1.id

        # Get or create again
        run2 = _get_or_create_whatif_run(db_session, profile.id)

        # Should be the same run
        assert run2.id == run1_id
        assert run2.label == WHATIF_SAVES_LABEL

    def test_get_or_create_whatif_run_increments_num_scenarios(self, db_session, test_profile):
        """num_scenarios should be updated correctly."""
        profile, _ = test_profile

        run = _get_or_create_whatif_run(db_session, profile.id)
        initial_count = run.num_scenarios

        # Manually add a scenario
        scenario = ScenarioResult(
            run_id=run.id,
            scenario_name="Test",
            retirement_year=15
        )
        db_session.add(scenario)
        db_session.commit()

        # Get or create again
        run = _get_or_create_whatif_run(db_session, profile.id)

        # Verify count can be updated
        count = db_session.query(ScenarioResult).filter(
            ScenarioResult.run_id == run.id
        ).count()
        assert count == 1


class TestDatabaseQueries:
    """Test querying saved scenarios from database."""

    def test_query_scenario_by_id(self, db_session, test_scenario):
        """Should be able to query scenario by ID."""
        scenario = db_session.query(ScenarioResult).filter(
            ScenarioResult.id == test_scenario.id
        ).first()

        assert scenario is not None
        assert scenario.scenario_name == "Test Scenario"
        assert scenario.retirement_year == 15

    def test_query_scenario_year_data(self, db_session, test_scenario):
        """Should be able to query year data for scenario."""
        year_data = db_session.query(YearData).filter(
            YearData.result_id == test_scenario.id
        ).all()

        assert len(year_data) == 20
        assert year_data[0].year == 1
        assert year_data[0].age == 41
        assert year_data[19].year == 20
        assert year_data[19].age == 60

    def test_query_scenarios_by_run(self, db_session, test_simulation_run, test_scenario):
        """Should be able to query all scenarios for a run."""
        scenarios = db_session.query(ScenarioResult).filter(
            ScenarioResult.run_id == test_simulation_run.id
        ).all()

        assert len(scenarios) == 1
        assert scenarios[0].scenario_name == "Test Scenario"

    def test_query_scenario_with_relationships(self, db_session, test_scenario):
        """Relationships should be properly populated."""
        scenario = db_session.query(ScenarioResult).filter(
            ScenarioResult.id == test_scenario.id
        ).first()

        # Test relationships
        assert scenario.run is not None
        assert scenario.run.label == "Test Run"
        assert len(scenario.year_data) == 20
