"""Load scenario nodes from JSON config.

A ScenarioNode represents a node in a scenario inheritance tree, where each node
can override fields from its parent and control event composition.

This module loads scenario_nodes.json and returns a dict[str, ScenarioNode],
validating the tree structure (no cycles, all parents exist, all roots have base_scenario).
"""

import json
from pathlib import Path
from models import ScenarioNode, Mortgage, Event
from scenarios import load_scenarios


_SCENARIO_NODES_FILE = Path(__file__).parent / "scenario_nodes.json"


def _node_from_dict(d: dict, all_scenarios: dict) -> ScenarioNode:
    """Parse a scenario node dict from JSON into a ScenarioNode object.

    Args:
        d: dict with keys 'name', optionally 'base_scenario' (root) or 'parent' (child),
           optional overrides and events
        all_scenarios: dict[str, Scenario] loaded from scenarios.json

    Returns:
        ScenarioNode object (not yet resolved; resolution happens via resolve(all_nodes))
    """
    # Root node: base_scenario is resolved from scenarios.json
    base_scenario = None
    if "base_scenario" in d:
        scenario_name = d["base_scenario"]
        if scenario_name not in all_scenarios:
            raise ValueError(f"base_scenario '{scenario_name}' not found in scenarios.json")
        base_scenario = all_scenarios[scenario_name]

    # Child node: parent_name is a string key into all_nodes (validated later)
    parent_name = d.get("parent", None)

    # Parse events
    events = [
        Event(
            year=e["year"],
            portfolio_injection=e["portfolio_injection"],
            description=e.get("description", "")
        )
        for e in d.get("events", [])
    ]

    # Parse event_mode (default: "append")
    event_mode = d.get("event_mode", "append")
    if event_mode not in ("append", "replace"):
        raise ValueError(f"event_mode must be 'append' or 'replace', got '{event_mode}'")

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

    return ScenarioNode(
        name=d["name"],
        base_scenario=base_scenario,
        parent_name=parent_name,
        monthly_income=d.get("monthly_income"),
        monthly_expenses=d.get("monthly_expenses"),
        age=d.get("age"),
        initial_portfolio=d.get("initial_portfolio"),
        return_rate=d.get("return_rate"),
        withdrawal_rate=d.get("withdrawal_rate"),
        currency=d.get("currency"),
        mortgage=mortgage,
        event_mode=event_mode,
        events=events,
    )


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
                # This should have been caught above, but be defensive
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
        path: Path to scenario_nodes.json (defaults to finance_planner/scenario_nodes.json)

    Returns:
        dict[str, ScenarioNode] where keys are node names

    Raises:
        FileNotFoundError: if the file does not exist
        ValueError: if the tree has cycles, missing parents, or other validation errors
    """
    all_scenarios = load_scenarios()

    with open(path) as f:
        data = json.load(f)

    nodes = {}
    for node_dict in data.get("scenario_nodes", []):
        node = _node_from_dict(node_dict, all_scenarios)
        nodes[node.name] = node

    # Validate the tree
    _validate_nodes(nodes)

    return nodes
