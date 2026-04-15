"""
JSON → SQLite Migration Script

Idempotent migration that:
1. Reads scenarios.json → inserts into scenario_definitions + child tables
2. Reads settings.json → inserts into profile_settings
3. Reads scenario_nodes.json → inserts into scenario_nodes + child tables
4. Links ScenarioResults to their definitions by name
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

# Add paths for domain imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from models import (
    Profile, ScenarioDefinition, ScenarioEvent, ScenarioMortgage, ScenarioPension,
    ProfileSettings, ScenarioNode, ScenarioNodeEvent, ScenarioNodeMortgage, ScenarioNodePension,
    ScenarioResult, SimulationRun
)
from infrastructure.data_layer import get_scenarios_path, get_settings_path, get_scenario_nodes_path
from infrastructure.parsers import parse_scenario, parse_mortgage, parse_events, parse_pension, parse_scenario_node
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown


def run_migration(db: Session) -> None:
    """Run the JSON → DB migration. Idempotent: safe to call multiple times."""

    # Add scenario_id column to scenario_results if it doesn't exist
    from sqlalchemy import text, inspect
    inspector = inspect(db.bind)
    columns = [c['name'] for c in inspector.get_columns('scenario_results')]
    if 'scenario_id' not in columns:
        print("  Adding scenario_id column to scenario_results...")
        db.execute(text("ALTER TABLE scenario_results ADD COLUMN scenario_id INTEGER"))
        db.commit()

    # Add historical_start_year column to scenario_definitions if it doesn't exist
    columns = [c['name'] for c in inspector.get_columns('scenario_definitions')]
    if 'historical_start_year' not in columns:
        print("  Adding historical_start_year column to scenario_definitions...")
        db.execute(text("ALTER TABLE scenario_definitions ADD COLUMN historical_start_year INTEGER"))
        db.commit()

    # Add historical_index column to scenario_definitions if it doesn't exist
    columns = [c['name'] for c in inspector.get_columns('scenario_definitions')]
    if 'historical_index' not in columns:
        print("  Adding historical_index column to scenario_definitions...")
        db.execute(text("ALTER TABLE scenario_definitions ADD COLUMN historical_index TEXT"))
        db.commit()

    # Add retirement_lifestyle columns to scenario_definitions if they don't exist
    columns = [c['name'] for c in inspector.get_columns('scenario_definitions')]
    if 'retirement_lifestyle_mode' not in columns:
        print("  Adding retirement_lifestyle_mode column to scenario_definitions...")
        db.execute(text("ALTER TABLE scenario_definitions ADD COLUMN retirement_lifestyle_mode TEXT"))
        db.commit()
    if 'retirement_lifestyle_age' not in columns:
        print("  Adding retirement_lifestyle_age column to scenario_definitions...")
        db.execute(text("ALTER TABLE scenario_definitions ADD COLUMN retirement_lifestyle_age INTEGER"))
        db.commit()
    if 'partial_retirement_income' not in columns:
        print("  Adding partial_retirement_income column to scenario_definitions...")
        db.execute(text("ALTER TABLE scenario_definitions ADD COLUMN partial_retirement_income REAL"))
        db.commit()

    # Add retirement and active_income columns to year_data if they don't exist
    columns = [c['name'] for c in inspector.get_columns('year_data')]
    if 'is_retired' not in columns:
        print("  Adding is_retired column to year_data...")
        db.execute(text("ALTER TABLE year_data ADD COLUMN is_retired BOOLEAN DEFAULT 0"))
        db.commit()
    if 'active_income' not in columns:
        print("  Adding active_income column to year_data...")
        db.execute(text("ALTER TABLE year_data ADD COLUMN active_income REAL DEFAULT 0.0"))
        db.commit()

    # Check if migration has already run
    if db.query(ScenarioDefinition).first():
        print("✓ Migration already completed (scenario_definitions table has rows)")
        # Still link scenario_results if not already linked
        link_scenario_results(db)
        return

    profiles = db.query(Profile).all()

    for profile in profiles:
        print(f"\nMigrating profile: {profile.name}")

        # Step 1: Migrate scenarios.json
        migrate_scenarios(db, profile)

        # Step 2: Migrate settings.json
        migrate_settings(db, profile)

        # Step 3: Migrate scenario_nodes.json
        migrate_scenario_nodes(db, profile)

    # Step 4: Link ScenarioResults to definitions
    link_scenario_results(db)

    print("\n✓ Migration complete!")


def migrate_scenarios(db: Session, profile: Profile) -> None:
    """Migrate scenarios.json to scenario_definitions + child tables."""
    scenarios_path = get_scenarios_path(profile.name)

    if not scenarios_path.exists():
        print(f"  ⚠ scenarios.json not found at {scenarios_path}")
        return

    with open(scenarios_path) as f:
        data = json.load(f)

    default_return_rate = 0.07
    default_withdrawal_rate = 0.04

    # Try to load settings for defaults
    settings_path = get_settings_path(profile.name)
    if settings_path.exists():
        with open(settings_path) as f:
            settings = json.load(f)
            default_return_rate = settings.get("simulation", {}).get("return_rate", 0.07)
            default_withdrawal_rate = settings.get("simulation", {}).get("withdrawal_rate", 0.04)

    for scenario_dict in data.get("scenarios", []):
        # Parse the scenario
        scenario = parse_scenario(scenario_dict, default_return_rate, default_withdrawal_rate)

        # Insert ScenarioDefinition
        definition = ScenarioDefinition(
            profile_id=profile.id,
            name=scenario_dict["name"],
            monthly_income=json.dumps(scenario.monthly_income.components),
            monthly_expenses=json.dumps(scenario.monthly_expenses.components),
            initial_portfolio=scenario.initial_portfolio,
            age=scenario.age,
            currency=scenario.currency,
            return_rate=scenario.return_rate,
            historical_start_year=scenario_dict.get("historical_start_year"),
            withdrawal_rate=scenario.withdrawal_rate,
            retirement_mode=scenario.retirement_mode,
            saved_from=scenario_dict.get("saved_from"),
            saved_at=scenario_dict.get("saved_at"),
            is_deleted=scenario_dict.get("is_deleted", False),
        )
        db.add(definition)
        db.flush()

        # Insert ScenarioEvents
        for event in scenario.events:
            db.add(ScenarioEvent(
                scenario_id=definition.id,
                year=event.year,
                portfolio_injection=event.portfolio_injection,
                description=event.description,
            ))

        # Insert ScenarioMortgage (zero or one)
        if scenario.mortgage:
            db.add(ScenarioMortgage(
                scenario_id=definition.id,
                principal=scenario.mortgage.principal,
                annual_rate=scenario.mortgage.annual_rate,
                duration_years=scenario.mortgage.duration_years,
                currency=scenario.mortgage.currency,
            ))

        # Insert ScenarioPension (zero or one)
        if scenario.pension:
            db.add(ScenarioPension(
                scenario_id=definition.id,
                initial_value=scenario.pension.initial_value,
                monthly_contribution=scenario.pension.monthly_contribution,
                annual_growth_rate=scenario.pension.annual_growth_rate,
                accessible_at_age=scenario.pension.accessible_at_age,
            ))

    db.commit()
    count = db.query(ScenarioDefinition).filter(ScenarioDefinition.profile_id == profile.id).count()
    print(f"  ✓ Migrated {count} scenarios from scenarios.json")


def migrate_settings(db: Session, profile: Profile) -> None:
    """Migrate settings.json to profile_settings."""
    settings_path = get_settings_path(profile.name)

    if not settings_path.exists():
        print(f"  ⚠ settings.json not found at {settings_path}")
        return

    with open(settings_path) as f:
        data = json.load(f)

    sim = data.get("simulation", {})
    output = data.get("output", {})

    settings = ProfileSettings(
        profile_id=profile.id,
        years=sim.get("years", 30),
        return_rate=sim.get("return_rate", 0.05),
        withdrawal_rate=sim.get("withdrawal_rate", 0.04),
        show_fields=json.dumps(output.get("show_fields", [])),
    )
    db.add(settings)
    db.commit()
    print(f"  ✓ Migrated settings from settings.json")


def migrate_scenario_nodes(db: Session, profile: Profile) -> None:
    """Migrate scenario_nodes.json to scenario_nodes + child tables."""
    nodes_path = get_scenario_nodes_path(profile.name)

    if not nodes_path.exists():
        print(f"  ⚠ scenario_nodes.json not found at {nodes_path}")
        return

    with open(nodes_path) as f:
        data = json.load(f)

    # Get all scenarios for resolving base_scenario references
    scenarios = db.query(ScenarioDefinition).filter(ScenarioDefinition.profile_id == profile.id).all()
    scenarios_by_name = {s.name: s for s in scenarios}

    # Parse nodes
    node_dicts = data.get("nodes", data.get("scenario_nodes", []))

    # First pass: create all nodes
    nodes_by_name = {}
    for node_dict in node_dicts:
        # Parse the node using existing parser (but we need to handle base_scenario differently)
        node_name = node_dict["name"]

        # For base_scenario, we need to look up the ScenarioDefinition ID instead of the Scenario object
        base_scenario_id = None
        if "base_scenario" in node_dict:
            base_scenario_name = node_dict["base_scenario"]
            if base_scenario_name in scenarios_by_name:
                base_scenario_id = scenarios_by_name[base_scenario_name].id

        # Parse income/expenses if present
        monthly_income = None
        monthly_expenses = None
        if "monthly_income" in node_dict:
            breakdown = parse_income_breakdown(node_dict["monthly_income"])
            monthly_income = json.dumps(breakdown.components)
        if "monthly_expenses" in node_dict:
            breakdown = parse_expense_breakdown(node_dict["monthly_expenses"])
            monthly_expenses = json.dumps(breakdown.components)

        # Create node (parent_id will be set in second pass)
        node = ScenarioNode(
            profile_id=profile.id,
            name=node_name,
            base_scenario_id=base_scenario_id,
            parent_id=None,  # Will be set in second pass
            event_mode=node_dict.get("event_mode", "append"),
            age=node_dict.get("age"),
            initial_portfolio=node_dict.get("initial_portfolio"),
            return_rate=node_dict.get("return_rate"),
            withdrawal_rate=node_dict.get("withdrawal_rate"),
            currency=node_dict.get("currency"),
            retirement_mode=node_dict.get("retirement_mode"),
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
        )
        db.add(node)
        nodes_by_name[node_name] = (node, node_dict)

    db.commit()

    # Second pass: set parent relationships and add child events/mortgage/pension
    for node_name, (node, node_dict) in nodes_by_name.items():
        # Set parent_id if this is a child node
        if "parent" in node_dict:
            parent_name = node_dict["parent"]
            if parent_name in nodes_by_name:
                parent_node, _ = nodes_by_name[parent_name]
                node.parent_id = parent_node.id
                db.add(node)

        # Add events
        events = parse_events(node_dict.get("events", []))
        for event in events:
            db.add(ScenarioNodeEvent(
                node_id=node.id,
                year=event.year,
                portfolio_injection=event.portfolio_injection,
                description=event.description,
            ))

        # Add mortgage (zero or one)
        mortgage = parse_mortgage(node_dict.get("mortgage"))
        if mortgage:
            db.add(ScenarioNodeMortgage(
                node_id=node.id,
                principal=mortgage.principal,
                annual_rate=mortgage.annual_rate,
                duration_years=mortgage.duration_years,
                currency=mortgage.currency,
            ))

        # Add pension (zero or one)
        pension = parse_pension(node_dict.get("pension"))
        if pension:
            db.add(ScenarioNodePension(
                node_id=node.id,
                initial_value=pension.initial_value,
                monthly_contribution=pension.monthly_contribution,
                annual_growth_rate=pension.annual_growth_rate,
                accessible_at_age=pension.accessible_at_age,
            ))

    db.commit()
    count = db.query(ScenarioNode).filter(ScenarioNode.profile_id == profile.id).count()
    print(f"  ✓ Migrated {count} scenario nodes from scenario_nodes.json")


def link_scenario_results(db: Session) -> None:
    """Link ScenarioResults to their definitions by matching scenario_name."""
    results = db.query(ScenarioResult).filter(ScenarioResult.scenario_id == None).all()

    linked_count = 0
    for result in results:
        # Find the profile for this result via the SimulationRun
        run = db.query(SimulationRun).filter(SimulationRun.id == result.run_id).first()
        if not run:
            continue

        # Find matching definition by profile + scenario_name
        definition = db.query(ScenarioDefinition).filter(
            ScenarioDefinition.profile_id == run.profile_id,
            ScenarioDefinition.name == result.scenario_name
        ).first()

        if definition:
            result.scenario_id = definition.id
            db.add(result)
            linked_count += 1

    db.commit()
    print(f"  ✓ Linked {linked_count} scenario results to definitions")


def parse_income_breakdown(value) -> IncomeBreakdown:
    """Helper to parse income (reuse from parsers.py)."""
    if isinstance(value, (int, float)):
        return IncomeBreakdown(components={"income": float(value)})
    if isinstance(value, dict):
        return IncomeBreakdown(components={k: float(v) for k, v in value.items()})
    raise ValueError(f"monthly_income must be a number or dict, got {type(value)}")


def parse_expense_breakdown(value) -> ExpenseBreakdown:
    """Helper to parse expenses (reuse from parsers.py)."""
    if isinstance(value, (int, float)):
        return ExpenseBreakdown(components={"expenses": float(value)})
    if isinstance(value, dict):
        return ExpenseBreakdown(components={k: float(v) for k, v in value.items()})
    raise ValueError(f"monthly_expenses must be a number or dict, got {type(value)}")
