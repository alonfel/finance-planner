"""Load persons from JSON config.

A Person wraps a base Scenario with optional overrides, enabling scenario reuse.
This module loads persons.json and returns a dict[str, Person].
"""

import json
from pathlib import Path
from models import Person, Mortgage, Event
from scenarios import load_scenarios


_PERSONS_FILE = Path(__file__).parent / "persons.json"


def _person_from_dict(d: dict, all_scenarios: dict) -> Person:
    """Parse a person dict from JSON into a Person object.

    Args:
        d: dict with keys 'name', 'base_scenario', optional overrides (monthly_income, etc.)
        all_scenarios: dict[str, Scenario] loaded from scenarios.json

    Returns:
        Person object with resolved base_scenario reference
    """
    base_scenario = all_scenarios[d["base_scenario"]]

    # Parse extra_events
    extra_events = [
        Event(
            year=e["year"],
            portfolio_injection=e["portfolio_injection"],
            description=e.get("description", "")
        )
        for e in d.get("extra_events", [])
    ]

    # Parse replace_events (only if present)
    replace_events = None
    if "replace_events" in d:
        replace_events = [
            Event(
                year=e["year"],
                portfolio_injection=e["portfolio_injection"],
                description=e.get("description", "")
            )
            for e in d["replace_events"]
        ]

    # Parse mortgage (only if present)
    mortgage = None
    if d.get("mortgage"):
        m = d["mortgage"]
        mortgage = Mortgage(
            principal=m["principal"],
            annual_rate=m["annual_rate"],
            duration_years=m["duration_years"],
            currency=m.get("currency", "ILS")
        )

    return Person(
        name=d["name"],
        base_scenario=base_scenario,
        monthly_income=d.get("monthly_income"),
        monthly_expenses=d.get("monthly_expenses"),
        age=d.get("age"),
        initial_portfolio=d.get("initial_portfolio"),
        return_rate=d.get("return_rate"),
        withdrawal_rate=d.get("withdrawal_rate"),
        currency=d.get("currency"),
        mortgage=mortgage,
        extra_events=extra_events,
        replace_events=replace_events,
    )


def load_persons(path: Path = _PERSONS_FILE) -> dict[str, Person]:
    """Load all persons from JSON file, keyed by name.

    Args:
        path: Path to persons.json (defaults to finance_planner/persons.json)

    Returns:
        dict[str, Person] where keys are person names
    """
    all_scenarios = load_scenarios()
    with open(path) as f:
        data = json.load(f)
    return {p["name"]: _person_from_dict(p, all_scenarios) for p in data["persons"]}
