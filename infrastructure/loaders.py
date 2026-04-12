"""Configuration loaders and settings management."""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

from domain.models import Scenario, ScenarioNode
from infrastructure.parsers import parse_scenario, parse_scenario_node
from infrastructure.data_layer import (
    migrate_to_data_layer,
    get_settings_path,
    get_scenarios_path,
    get_scenario_nodes_path,
    DEFAULT_PROFILE,
    ACTIVE_PROFILE,
)


# Auto-migrate legacy files to profile-based structure (one-shot, idempotent)
migrate_to_data_layer(DEFAULT_PROFILE)

# Default file paths (now point to profile-based data layer, using active profile)
_SETTINGS_FILE = get_settings_path(ACTIVE_PROFILE)
_SCENARIOS_FILE = get_scenarios_path(ACTIVE_PROFILE)
_SCENARIO_NODES_FILE = get_scenario_nodes_path(ACTIVE_PROFILE)


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
    """Load simulation settings from JSON file.

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


def load_scenarios(path: Path = _SCENARIOS_FILE) -> dict[str, Scenario]:
    """Load all scenarios from JSON file.

    Args:
        path: Path to scenarios.json file

    Returns:
        Dictionary keyed by scenario name
    """
    with open(path) as f:
        data = json.load(f)

    # Use SETTINGS for default rates
    return {s["name"]: parse_scenario(s, SETTINGS.return_rate, SETTINGS.withdrawal_rate)
            for s in data["scenarios"]}


def _validate_nodes(nodes: dict[str, ScenarioNode]) -> None:
    """Validate the scenario node tree.

    Checks:
    - All parent_name references exist in the dict
    - No cycles (walk each ancestor chain, detect repeated names)
    - All root nodes have base_scenario set

    Args:
        nodes: dict[str, ScenarioNode] to validate

    Raises:
        ValueError if any validation check fails
    """
    for name, node in nodes.items():
        # Check parent_name references exist
        if node.parent_name is not None:
            if node.parent_name not in nodes:
                raise ValueError(
                    f"Node '{name}' references non-existent parent '{node.parent_name}'"
                )

        # Check no cycles and that all roots have base_scenario
        visited = set()
        current = node
        while current.parent_name is not None:
            if current.name in visited:
                raise ValueError(f"Cycle detected in scenario tree involving node '{current.name}'")
            visited.add(current.name)

            parent_name = current.parent_name
            if parent_name not in nodes:
                raise ValueError(f"Parent '{parent_name}' not found")

            current = nodes[parent_name]

        # current is now the root of this chain; it must have base_scenario
        if current.base_scenario is None:
            root_chain = " -> ".join(visited) + (f" -> {current.name}" if visited else current.name)
            raise ValueError(
                f"Root node '{current.name}' (ancestor of '{name}') has no base_scenario set"
            )


def load_scenario_nodes(path: Path = _SCENARIO_NODES_FILE) -> dict[str, ScenarioNode]:
    """Load all scenario nodes from JSON file, keyed by name.

    Args:
        path: Path to scenario_nodes.json (defaults to scenario_analysis/scenario_nodes.json)

    Returns:
        dict[str, ScenarioNode] where keys are node names

    Raises:
        FileNotFoundError: if the file does not exist
        ValueError: if the tree has cycles, missing parents, or other validation errors
    """
    # Load scenarios from the same profile's scenarios file
    all_scenarios = load_scenarios(get_scenarios_path(ACTIVE_PROFILE))

    with open(path) as f:
        data = json.load(f)

    nodes = {}
    # Support both "scenario_nodes" (legacy) and "nodes" (new) keys
    node_list = data.get("scenario_nodes") or data.get("nodes", [])
    for node_dict in node_list:
        node = parse_scenario_node(node_dict, all_scenarios)
        nodes[node.name] = node

    # Validate the tree
    _validate_nodes(nodes)

    return nodes


# Loaded at import time (singleton)
SETTINGS = load_settings()
