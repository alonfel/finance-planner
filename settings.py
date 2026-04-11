import json
from pathlib import Path
from dataclasses import dataclass


_SETTINGS_FILE = Path(__file__).parent / "settings.json"


@dataclass
class Settings:
    """Global simulation settings."""
    years: int = 40  # Fallback default if not in JSON


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
    return Settings(
        years=sim.get("years", 40),
    )


# Loaded at import time
SETTINGS = load_settings()
