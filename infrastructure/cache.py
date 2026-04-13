"""Cache management: serialization, deserialization, and loading/saving."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from domain.simulation import SimulationResult, YearData


def year_data_to_dict(year_data: YearData) -> Dict[str, Any]:
    """Convert YearData object to a serializable dict.

    Args:
        year_data: YearData object

    Returns:
        Dictionary with year, age, income, expenses, net_savings, portfolio, required_capital, mortgage_active, pension_value, pension_accessible
    """
    return {
        "year": year_data.year,
        "age": year_data.age,
        "income": year_data.income,
        "expenses": year_data.expenses,
        "net_savings": year_data.net_savings,
        "portfolio": year_data.portfolio,
        "required_capital": year_data.required_capital,
        "mortgage_active": year_data.mortgage_active,
        "pension_value": year_data.pension_value,
        "pension_accessible": year_data.pension_accessible,
    }


def simulation_result_to_dict(result: SimulationResult) -> Dict[str, Any]:
    """Convert SimulationResult object to a serializable dict.

    Args:
        result: SimulationResult object

    Returns:
        Dictionary with scenario_name, retirement_year, and year_data list
    """
    return {
        "scenario_name": result.scenario_name,
        "retirement_year": result.retirement_year,
        "year_data": [year_data_to_dict(yd) for yd in result.year_data],
    }


def dict_to_simulation_result(data: Dict[str, Any]) -> SimulationResult:
    """Reconstruct a SimulationResult from cached dict data.

    This is the inverse of simulation_result_to_dict, converting JSON back into
    in-memory object structure.

    Args:
        data: Dictionary with scenario_name, retirement_year, year_data

    Returns:
        SimulationResult object
    """
    year_data_list = []
    for yd in data.get("year_data", []):
        yd_obj = YearData(
            year=yd["year"],
            age=yd.get("age", 0),  # Backward compat: use 0 if missing from old cache
            income=yd["income"],
            expenses=yd["expenses"],
            net_savings=yd["net_savings"],
            portfolio=yd["portfolio"],
            required_capital=yd["required_capital"],
            mortgage_active=yd["mortgage_active"],
            pension_value=yd.get("pension_value", 0.0),
            pension_accessible=yd.get("pension_accessible", False),
        )
        year_data_list.append(yd_obj)

    result = SimulationResult(
        scenario_name=data["scenario_name"],
        retirement_year=data["retirement_year"],
        year_data=year_data_list,
    )
    return result


def save_cache(results: Dict[str, Dict[str, Any]], path: Path) -> None:
    """Save simulation results to cache file.

    Args:
        results: Dictionary mapping scenario names to simulation result dicts
        path: Path to write cache file to
    """
    cache_data = {
        "generated_at": datetime.now().isoformat(),
        "num_scenarios": len(results),
        "results": results,
    }

    with open(path, "w") as f:
        json.dump(cache_data, f, indent=2)

    print(f"✓ Cache saved to {path.name}")
    print(f"  Generated: {cache_data['generated_at']}")
    print(f"  Scenarios: {cache_data['num_scenarios']}")


def load_cache(path: Path) -> Optional[Dict[str, Dict[str, Any]]]:
    """Load cached simulation results from JSON.

    Returns None if file doesn't exist or cannot be parsed.

    Args:
        path: Path to cache file

    Returns:
        Dictionary mapping scenario names to result dicts, or None if not found
    """
    if not path.exists():
        return None

    try:
        with open(path) as f:
            cache_data = json.load(f)
        return cache_data.get("results", {})
    except Exception as e:
        print(f"⚠️  Could not load cache: {e}")
        return None
