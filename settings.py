import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List


_SETTINGS_FILE = Path(__file__).parent / "settings.json"


@dataclass
class OutputConfig:
    """Configuration for what scenario parameters to display in output."""
    show_fields: List[str] = field(default_factory=lambda: [
        "income_expenses",
        "mortgage_details",
        "events",
        "rates_settings"
    ])


@dataclass
class Settings:
    """Global simulation settings."""
    years: int = 40  # Fallback default if not in JSON
    return_rate: float = 0.07  # Annual portfolio return rate
    withdrawal_rate: float = 0.04  # Safe withdrawal rate (4% rule)
    output: OutputConfig = field(default_factory=OutputConfig)


def load_settings(path: Path = _SETTINGS_FILE) -> Settings:
    """
    Load simulation settings from JSON file.

    Args:
        path: Path to settings.json file

    Returns:
        Settings object with loaded values
    """
    with open(path) as f:
        data = json.load(f)

    sim = data.get("simulation", {})
    output_data = data.get("output", {})

    return Settings(
        years=sim.get("years", 40),
        return_rate=sim.get("return_rate", 0.07),
        withdrawal_rate=sim.get("withdrawal_rate", 0.04),
        output=OutputConfig(
            show_fields=output_data.get("show_fields", [
                "income_expenses",
                "mortgage_details",
                "events",
                "rates_settings"
            ])
        )
    )


# Loaded at import time
SETTINGS = load_settings()
