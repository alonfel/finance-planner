import json
from pathlib import Path
from models import Scenario, Mortgage, Event
from settings import SETTINGS


_SCENARIOS_FILE = Path(__file__).parent / "scenarios.json"


def _scenario_from_dict(d: dict) -> Scenario:
    """Convert a scenario dictionary to a Scenario object."""
    mortgage = None
    if d.get("mortgage"):
        m = d["mortgage"]
        mortgage = Mortgage(
            principal=m["principal"],
            annual_rate=m["annual_rate"],
            duration_years=m["duration_years"],
            currency=m.get("currency", "ILS"),
        )

    events = []
    for e in d.get("events", []):
        events.append(Event(
            year=e["year"],
            portfolio_injection=e["portfolio_injection"],
            description=e.get("description", ""),
        ))

    return Scenario(
        name=d["name"],
        monthly_income=d["monthly_income"],
        monthly_expenses=d["monthly_expenses"],
        mortgage=mortgage,
        initial_portfolio=d.get("initial_portfolio", 0.0),
        return_rate=d.get("return_rate", SETTINGS.return_rate),
        withdrawal_rate=d.get("withdrawal_rate", SETTINGS.withdrawal_rate),
        currency=d.get("currency", "ILS"),
        age=d.get("age", 30),
        events=events,
    )


def load_scenarios(path: Path = _SCENARIOS_FILE) -> dict[str, Scenario]:
    """
    Load all scenarios from JSON file.

    Args:
        path: Path to scenarios.json file

    Returns:
        Dictionary keyed by scenario name
    """
    with open(path) as f:
        data = json.load(f)

    return {s["name"]: _scenario_from_dict(s) for s in data["scenarios"]}


# Convenience aliases — loaded from scenarios.json at import time
_all_scenarios = load_scenarios()
SCENARIO_A = _all_scenarios["Baseline"]
SCENARIO_B = _all_scenarios["Buy Apartment"]
