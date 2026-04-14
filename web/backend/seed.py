#!/usr/bin/env python
"""
Seed the database from existing Alon profile cache and setup.
"""
import json
import os
from database import init_db, SessionLocal
from models import User, Profile, SimulationRun, ScenarioResult, YearData
from auth import hash_password
from migration import link_scenario_results

def seed_database():
    """Seed database with Alon profile and cache data"""
    init_db()
    db = SessionLocal()

    try:
        # Check if already seeded
        existing_profile = db.query(Profile).filter(Profile.name == "alon").first()
        if existing_profile:
            print("Database already seeded. Skipping.")
            return

        # Create default user
        user = User(
            username="alon",
            password_hash=hash_password("alon123")
        )
        db.add(user)
        db.commit()
        print("✓ Created user: alon")

        # Load and create profile
        profile_json_path = "/Users/alon/Documents/finance_planner/data/profiles/alon/profile.json"
        with open(profile_json_path, "r") as f:
            profile_data = json.load(f)

        profile = Profile(
            name="alon",
            display_name=profile_data.get("name", "Alon"),
            description=profile_data.get("description", ""),
            created_at=profile_data.get("created_at", "2026-04-01")
        )
        db.add(profile)
        db.commit()
        print(f"✓ Created profile: {profile.display_name}")

        # Load cache
        cache_path = "/Users/alon/Documents/finance_planner/data/profiles/alon/analyses/cache/simulation_cache.json"
        with open(cache_path, "r") as f:
            cache_data = json.load(f)

        # Create simulation run
        run = SimulationRun(
            profile_id=profile.id,
            generated_at=cache_data["generated_at"],
            num_scenarios=cache_data["num_scenarios"],
            label=None
        )
        db.add(run)
        db.commit()
        print(f"✓ Created simulation run (generated at {run.generated_at})")

        # Create scenario results and year data
        scenario_count = 0
        year_count = 0
        for scenario_name, scenario_result in cache_data["results"].items():
            scenario = ScenarioResult(
                run_id=run.id,
                scenario_name=scenario_name,
                retirement_year=scenario_result.get("retirement_year")
            )
            db.add(scenario)
            db.commit()
            scenario_count += 1

            for year_data in scenario_result.get("year_data", []):
                yd = YearData(
                    result_id=scenario.id,
                    year=year_data["year"],
                    age=year_data["age"],
                    income=year_data["income"],
                    expenses=year_data["expenses"],
                    net_savings=year_data["net_savings"],
                    portfolio=year_data["portfolio"],
                    required_capital=year_data["required_capital"],
                    mortgage_active=year_data["mortgage_active"],
                    pension_value=year_data.get("pension_value", 0.0),
                    pension_accessible=year_data.get("pension_accessible", False)
                )
                db.add(yd)
                year_count += 1

            db.commit()

        print(f"✓ Created {scenario_count} scenarios with {year_count} year data rows")

        # Backfill scenario_id FKs for seeded scenarios
        link_scenario_results(db)
        print("✓ Linked scenarios to scenario_definitions")

        print("\n✅ Database seeded successfully!")
        print(f"   - User: alon / alon123")
        print(f"   - Profile: {profile.display_name}")
        print(f"   - Scenarios: {scenario_count}")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
