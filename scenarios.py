import json
from pathlib import Path
from models import Scenario, Mortgage


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

    return Scenario(
        name=d["name"],
        monthly_income=d["monthly_income"],
        monthly_expenses=d["monthly_expenses"],
        mortgage=mortgage,
        initial_portfolio=d.get("initial_portfolio", 0.0),
        return_rate=d.get("return_rate", 0.07),
        withdrawal_rate=d.get("withdrawal_rate", 0.04),
        currency=d.get("currency", "ILS"),
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
